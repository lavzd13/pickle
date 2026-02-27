from rest_framework import serializers
from .models import AccountDetail, Payment, PlaySession, Platform, Network, ProxyVpn, WalletProvider


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Network
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']


class ProxyVpnSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProxyVpn
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']


class WalletProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletProvider
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['created_at']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'withdraw_pass', 'min_balance', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class AccountDetailSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer(read_only=True)
    
    class Meta:
        model = AccountDetail
        fields = ['id', 'nick', 'email', 'phone', 'payment', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class PlaySessionSerializer(serializers.ModelSerializer):
    account_nick = serializers.CharField(source='account.nick', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    can_edit = serializers.SerializerMethodField()
    duration_display = serializers.CharField(read_only=True)

    class Meta:
        model = PlaySession
        fields = [
            'id', 'account', 'account_nick', 'session_date',
            'start_time', 'end_time', 'duration_display',
            'notes', 'created_by', 'created_by_username', 'can_edit',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_can_edit(self, obj):
        """Check if current user can edit this session"""
        request = self.context.get('request')
        if request and request.user:
            return obj.is_editable_by(request.user)
        return False

    def create(self, validated_data):
        """Set created_by to current user"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class PlaySessionCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating sessions"""

    class Meta:
        model = PlaySession
        fields = ['account', 'session_date', 'start_time', 'end_time', 'notes']

    def create(self, validated_data):
        """Set created_by to current user"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)
