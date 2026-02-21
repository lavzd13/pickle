from collections import defaultdict
from datetime import datetime, timedelta

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import AccountDetail, Payment, PlaySession, Platform, Network, ProxyVpn, WalletProvider
from .serializers import (
    AccountDetailSerializer,
    PaymentSerializer,
    PlaySessionSerializer,
    PlaySessionCreateSerializer,
    PlatformSerializer,
    NetworkSerializer,
    ProxyVpnSerializer,
    WalletProviderSerializer,
)
from .permissions import IsOwnerOrSuperuser, CanViewOldSessions


class PlatformViewSet(viewsets.ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsAuthenticated]


class NetworkViewSet(viewsets.ModelViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    permission_classes = [IsAuthenticated]


class ProxyVpnViewSet(viewsets.ModelViewSet):
    queryset = ProxyVpn.objects.all()
    serializer_class = ProxyVpnSerializer
    permission_classes = [IsAuthenticated]


class WalletProviderViewSet(viewsets.ModelViewSet):
    queryset = WalletProvider.objects.all()
    serializer_class = WalletProviderSerializer
    permission_classes = [IsAuthenticated]


class AccountDetailViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AccountDetail model.
    """
    queryset = AccountDetail.objects.all()
    serializer_class = AccountDetailSerializer
    permission_classes = [IsAuthenticated]


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payment model.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]


class PlaySessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PlaySession model with automatic 60-day retention filtering.
    """
    serializer_class = PlaySessionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperuser]
    
    def get_queryset(self):
        """
        Filter sessions based on user role:
        - Superusers: See all sessions (including old ones)
        - Regular users: See only their own sessions (within 60 days)
        """
        if self.request.user.is_superuser:
            # Superusers can see all sessions including old ones
            return PlaySession.objects.all_including_old()
        else:
            # Regular users only see their own sessions (auto-filtered to 60 days)
            return PlaySession.objects.filter(created_by=self.request.user)
    
    def get_serializer_class(self):
        """Use simplified serializer for create action"""
        if self.action == 'create':
            return PlaySessionCreateSerializer
        return PlaySessionSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user when creating a session"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_sessions(self, request):
        """Get all sessions created by the current user (within 60 days)"""
        sessions = PlaySession.objects.filter(created_by=request.user)
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanViewOldSessions])
    def old_sessions(self, request):
        """
        Get sessions older than 60 days (superuser only).
        This bypasses the automatic 60-day filter.
        """
        cutoff_date = timezone.now() - timedelta(days=60)
        old_sessions = PlaySession.objects.all_including_old().filter(session_date__lt=cutoff_date.date())
        serializer = self.get_serializer(old_sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_account(self, request):
        """Get sessions for a specific account (query param: account_id)"""
        account_id = request.query_params.get('account_id')
        if not account_id:
            return Response(
                {'error': 'account_id query parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(account_id=account_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def date_range(self, request):
        """
        Get sessions within a date range.
        Query params: start_date, end_date (format: YYYY-MM-DD)
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'Both start_date and end_date query parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            session_date__gte=start_date,
            session_date__lte=end_date
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get sessions grouped by account and date with total duration."""
        queryset = self.get_queryset().select_related('account', 'created_by')

        account_id = request.query_params.get('account_id')
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(session_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(session_date__lte=end_date)

        groups = defaultdict(list)
        for session in queryset.order_by('-session_date', '-start_time'):
            key = (session.account_id, str(session.session_date))
            groups[key].append(session)

        result = []
        for (acct_id, session_date), sessions in groups.items():
            # Merge overlapping intervals for accurate total
            intervals = []
            for s in sessions:
                start_dt = datetime.combine(s.session_date, s.start_time)
                end_dt = datetime.combine(s.session_date, s.end_time)
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)
                intervals.append((start_dt, end_dt))
            intervals.sort(key=lambda x: x[0])
            merged = [intervals[0]]
            for start, end in intervals[1:]:
                if start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            total_duration = sum((end - start for start, end in merged), timedelta())
            total_seconds = int(total_duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            result.append({
                'account_id': acct_id,
                'account_nick': sessions[0].account.nick,
                'session_date': session_date,
                'session_count': len(sessions),
                'total_duration_display': f"{hours}h {minutes}m" if hours else f"{minutes}m",
                'sessions': [
                    {
                        'id': s.id,
                        'start_time': str(s.start_time)[:5],
                        'end_time': str(s.end_time)[:5],
                        'duration_display': s.duration_display,
                    }
                    for s in sessions
                ],
            })

        result.sort(key=lambda x: x['session_date'], reverse=True)
        return Response(result)
