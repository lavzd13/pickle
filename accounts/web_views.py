from collections import defaultdict
from datetime import timedelta
import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from .models import PlaySession, AccountDetail, Payment, Location, Security, LastTransaction, PlayInfo, DepositWithdrawal
from django.db.models import Sum
from django.forms import modelformset_factory
from django.http import JsonResponse, HttpResponse
from .forms import PlaySessionForm, DaySessionForm, AccountDetailForm, PaymentForm, UserCreateForm, UserEditForm, PlatformForm, LocationForm, SecurityForm, LastTransactionForm


def gaussian_sample(min_val, max_val, median=None):
    """
    Generate random samples from a normal distribution.
    
    - If median is not provided, it's calculated as midpoint of min and max
    - σ = (max_val - min_val) / 6
    """
    mu = median if median is not None else (min_val + max_val) / 2
    sigma = (max_val - min_val) / 6

    res = 0
    value = random.gauss(mu, sigma)
    value = max(min_val, min(max_val, value))
    res = value

    return res

def calculate_play_info(account):
    days_of_the_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


    try:
        play_info = PlayInfo.objects.get(account=account)
    except PlayInfo.DoesNotExist:
        play_info = PlayInfo.objects.create(
            account=account,
            play_days_per_week=gaussian_sample(2, 7, 5.2),
            holiday_days_per_year=gaussian_sample(10, 35, 17),
            hours_per_day=gaussian_sample(2, 10, 4.5)
        )

    holiday_days_per_year = play_info.holiday_days_per_year

    # Reset old table to all -1
    for day in days_of_the_week:
        play_info.schedule_of_the_week[day] = -1

    # Select play days based on gaussian_sample(2, 7, 3.5) / 7 <= random.uniform(0, 1)
    for day in days_of_the_week:
        res = random.uniform(0, 1)
        if play_info.play_days_per_week / play_info.DAYS_OF_THE_WEEK >= res:
            play_info.schedule_of_the_week[day] = 0

    # Choose holiday days based on gaussian_sample(10, 35, 17) >= random.uniform(0, 1)
    for day in days_of_the_week:
        res = random.uniform(0, 1)
        if holiday_days_per_year / 365 >= res:
            play_info.schedule_of_the_week[day] = -1

    # Check if it's play day and set hours for it based on gaussian_sample(2, 10, 4.5)
    for day in days_of_the_week:
        if play_info.schedule_of_the_week[day] == -1:
            continue
        play_info.schedule_of_the_week[day] = gaussian_sample(2, 10, play_info.hours_per_day)
    play_info.save()


def is_superuser(user):
    return user.is_superuser


def _merge_intervals(sessions):
    """Merge overlapping time intervals and return total non-overlapping duration."""
    from datetime import datetime
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

    return sum((end - start for start, end in merged), timedelta())


def _group_sessions_by_day(sessions):
    """Group sessions by (account, date) and compute daily totals with overlap handling."""
    groups = defaultdict(list)
    for session in sessions.select_related('account', 'created_by').order_by('-session_date', '-start_time'):
        key = (session.account_id, session.session_date)
        groups[key].append(session)

    result = []
    for (account_id, session_date), day_sessions in groups.items():
        total_duration = _merge_intervals(day_sessions)
        total_seconds = int(total_duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        result.append({
            'account': day_sessions[0].account,
            'session_date': session_date,
            'sessions': day_sessions,
            'session_count': len(day_sessions),
            'total_duration': total_duration,
            'total_duration_display': f"{hours}h {minutes}m" if hours else f"{minutes}m",
            'created_by': day_sessions[0].created_by,
            'notes': '; '.join(s.notes for s in day_sessions if s.notes),
        })

    result.sort(key=lambda x: x['session_date'], reverse=True)
    return result


@login_required
def dashboard(request):
    """Dashboard showing overview of sessions"""
    if request.user.is_superuser:
        total_sessions = PlaySession.objects.all_including_old().count()
        recent_sessions = PlaySession.objects.all()
        accounts = AccountDetail.objects.all()
    else:
        total_sessions = PlaySession.objects.filter(created_by=request.user).count()
        recent_sessions = PlaySession.objects.filter(created_by=request.user)
        accounts = AccountDetail.objects.filter(play_sessions__created_by=request.user).distinct()

    daily_entries = _group_sessions_by_day(recent_sessions)[:10]

    context = {
        'total_sessions': total_sessions,
        'recent_sessions_count': recent_sessions.count(),
        'accounts_count': accounts.count(),
        'daily_entries': daily_entries,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def session_list(request):
    """List all sessions accessible to the user"""
    if request.user.is_superuser:
        sessions = PlaySession.objects.all_including_old().select_related('account', 'created_by')
    else:
        sessions = PlaySession.objects.filter(created_by=request.user).select_related('account', 'created_by')
    
    # Filter by account if specified
    account_id = request.GET.get('account')
    if account_id:
        sessions = sessions.filter(account_id=account_id)
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        sessions = sessions.filter(session_date__gte=start_date)
    if end_date:
        sessions = sessions.filter(session_date__lte=end_date)
    
    # Get accounts for filter dropdown
    if request.user.is_superuser:
        accounts = AccountDetail.objects.all()
    else:
        accounts = AccountDetail.objects.filter(play_sessions__created_by=request.user).distinct()
    
    daily_entries = _group_sessions_by_day(sessions)

    context = {
        'daily_entries': daily_entries,
        'accounts': accounts,
        'selected_account': account_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'accounts/session_list.html', context)


@login_required
def session_create(request):
    """Create a new session"""
    if request.method == 'POST':
        form = PlaySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.save()
            messages.success(request, 'Session created successfully!')
            return redirect('session_list')
    else:
        form = PlaySessionForm()
    
    return render(request, 'accounts/session_form.html', {'form': form, 'title': 'Create Session'})


@login_required
def session_edit(request, pk):
    """Edit an existing session"""
    if request.user.is_superuser:
        session = get_object_or_404(PlaySession.objects.all_including_old(), pk=pk)
    else:
        session = get_object_or_404(PlaySession, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = PlaySessionForm(request.POST, instance=session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Session updated successfully!')
            return redirect('session_list')
    else:
        form = PlaySessionForm(instance=session)
    
    return render(request, 'accounts/session_form.html', {
        'form': form, 
        'title': 'Edit Session',
        'session': session
    })


@login_required
def session_delete(request, pk):
    """Delete a session"""
    if request.user.is_superuser:
        session = get_object_or_404(PlaySession.objects.all_including_old(), pk=pk)
    else:
        session = get_object_or_404(PlaySession, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        session.delete()
        messages.success(request, 'Session deleted successfully!')
        return redirect('session_list')
    
    return render(request, 'accounts/session_confirm_delete.html', {'session': session})


@login_required
def manage_day_sessions(request, account_id, date):
    """Manage all sessions for a specific account on a specific date."""
    from datetime import datetime as dt
    account = get_object_or_404(AccountDetail, pk=account_id)
    session_date = dt.strptime(date, '%Y-%m-%d').date()

    # Permission: superuser or user who owns sessions for this account+date
    if not request.user.is_superuser:
        if not PlaySession.objects.filter(account=account, session_date=session_date, created_by=request.user).exists():
            messages.error(request, 'You do not have permission to manage these sessions.')
            return redirect('session_list')

    if request.user.is_superuser:
        queryset = PlaySession.objects.all_including_old().filter(account=account, session_date=session_date)
    else:
        queryset = PlaySession.objects.filter(account=account, session_date=session_date, created_by=request.user)

    DaySessionFormSet = modelformset_factory(
        PlaySession, form=DaySessionForm, extra=1, can_delete=True
    )

    if request.method == 'POST':
        formset = DaySessionFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for obj in instances:
                obj.account = account
                obj.session_date = session_date
                if not obj.created_by_id:
                    obj.created_by = request.user
                obj.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f'Sessions for {account.nick} on {session_date} updated!')
            return redirect('manage_day_sessions', account_id=account.id, date=date)
    else:
        formset = DaySessionFormSet(queryset=queryset)

    context = {
        'account': account,
        'session_date': session_date,
        'formset': formset,
    }
    return render(request, 'accounts/manage_day_sessions.html', context)


@login_required
@user_passes_test(is_superuser)
def account_list(request):
    """List all accounts (superuser only)"""
    accounts = AccountDetail.objects.all().select_related('payment')
    
    context = {
        'accounts': accounts,
    }
    return render(request, 'accounts/account_list.html', context)

@login_required
@user_passes_test(is_superuser)
def account_create(request):
    """Create a new account (superuser only)"""
    if request.method == 'POST':
        account_form = AccountDetailForm(request.POST)
        payment_form = PaymentForm(request.POST)
        location_form = LocationForm(request.POST)
        security_form = SecurityForm(request.POST)
        last_transaction_form = LastTransactionForm(request.POST, request.FILES)

        if (account_form.is_valid() and payment_form.is_valid() and
                location_form.is_valid() and
                security_form.is_valid() and last_transaction_form.is_valid()):
            account = account_form.save()

            payment = payment_form.save(commit=False)
            payment.account = account
            payment.save()

            location = location_form.save(commit=False)
            location.account = account
            location.save()

            security = security_form.save(commit=False)
            security.account = account
            security.save()

            last_transaction = last_transaction_form.save(commit=False)
            last_transaction.account = account
            last_transaction.save()

            if account.is_active:
                calculate_play_info(account)

            messages.success(request, f'Gaming account {account.nick} created successfully!')
            return redirect('account_list')
    else:
        account_form = AccountDetailForm()
        payment_form = PaymentForm()
        location_form = LocationForm()
        security_form = SecurityForm()
        last_transaction_form = LastTransactionForm()

    return render(request, 'accounts/account_form.html', {
        'account_form': account_form,
        'payment_form': payment_form,
        'location_form': location_form,
        'security_form': security_form,
        'last_transaction_form': last_transaction_form,
        'title': 'Create Gaming Account'
    })


@login_required
@user_passes_test(is_superuser)
def account_edit(request, pk):
    """Edit an account (superuser only)"""
    account = get_object_or_404(AccountDetail, pk=pk)
    payment = getattr(account, 'payment', None)
    location = getattr(account, 'location', None)
    security = getattr(account, 'security', None)
    last_transaction = getattr(account, 'last_transaction', None)

    if request.method == 'POST':
        account_form = AccountDetailForm(request.POST, instance=account)
        payment_form = PaymentForm(request.POST, instance=payment)
        location_form = LocationForm(request.POST, instance=location)
        security_form = SecurityForm(request.POST, instance=security)
        last_transaction_form = LastTransactionForm(request.POST, request.FILES, instance=last_transaction)

        if (account_form.is_valid() and payment_form.is_valid() and
                location_form.is_valid() and
                security_form.is_valid() and last_transaction_form.is_valid()):
            account = account_form.save()

            if payment:
                payment_form.save()
            else:
                payment = payment_form.save(commit=False)
                payment.account = account
                payment.save()

            if location:
                location_form.save()
            else:
                location = location_form.save(commit=False)
                location.account = account
                location.save()

            if security:
                security_form.save()
            else:
                security = security_form.save(commit=False)
                security.account = account
                security.save()

            if last_transaction:
                last_transaction_form.save()
            else:
                last_transaction = last_transaction_form.save(commit=False)
                last_transaction.account = account
                last_transaction.save()

            if account.is_active:
                calculate_play_info(account)

            messages.success(request, f'Gaming account {account.nick} updated successfully!')
            return redirect('account_list')
    else:
        account_form = AccountDetailForm(instance=account)
        payment_form = PaymentForm(instance=payment)
        location_form = LocationForm(instance=location)
        security_form = SecurityForm(instance=security)
        last_transaction_form = LastTransactionForm(instance=last_transaction)

    return render(request, 'accounts/account_form.html', {
        'account_form': account_form,
        'payment_form': payment_form,
        'location_form': location_form,
        'security_form': security_form,
        'last_transaction_form': last_transaction_form,
        'title': 'Edit Gaming Account',
        'account': account
    })


@login_required
@user_passes_test(is_superuser)
def account_delete(request, pk):
    """Delete an account (superuser only)"""
    account = get_object_or_404(AccountDetail, pk=pk)
    
    if request.method == 'POST':
        nick = account.nick
        account.delete()
        messages.success(request, f'Gaming account {nick} deleted successfully!')
        return redirect('account_list')
    
    return render(request, 'accounts/account_confirm_delete.html', {'account': account})


@login_required
@user_passes_test(is_superuser)
def account_sessions(request, pk):
    """View all sessions for a specific account including past 60 days (superuser only)"""
    account = get_object_or_404(AccountDetail, pk=pk)
    sessions = PlaySession.objects.all_including_old().filter(account=account)

    # Calculate stats
    cutoff_date = timezone.now() - timedelta(days=60)
    recent_sessions = sessions.filter(session_date__gte=cutoff_date.date())
    old_sessions = sessions.filter(session_date__lt=cutoff_date.date())

    daily_entries = _group_sessions_by_day(sessions)

    context = {
        'account': account,
        'daily_entries': daily_entries,
        'recent_sessions_count': recent_sessions.count(),
        'old_sessions_count': old_sessions.count(),
        'total_sessions': sessions.count(),
        'cutoff_date': cutoff_date.date(),
    }
    return render(request, 'accounts/account_sessions.html', context)


# System Users Management

@login_required
@user_passes_test(is_superuser)
def user_list(request):
    """List all system users (superuser only)"""
    users = User.objects.all().order_by('-is_superuser', 'username')
    
    context = {
        'users': users,
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
@user_passes_test(is_superuser)
def user_create(request):
    """Create a new system user (superuser only)"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            messages.success(request, f'System user {user.username} created successfully!')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Create System User'
    })


@login_required
@user_passes_test(is_superuser)
def user_edit(request, pk):
    """Edit a system user (superuser only)"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        
        if form.is_valid():
            user = form.save(commit=False)
            
            # Only update password if provided
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)
            
            user.save()
            
            messages.success(request, f'System user {user.username} updated successfully!')
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user)
    
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'title': 'Edit System User',
        'edit_user': user
    })


@login_required
@user_passes_test(is_superuser)
def user_delete(request, pk):
    """Delete a system user (superuser only)"""
    user = get_object_or_404(User, pk=pk)
    
    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'System user {username} deleted successfully!')
        return redirect('user_list')
    
    # Count sessions created by this user
    sessions_count = PlaySession.objects.all_including_old().filter(created_by=user).count()
    
    return render(request, 'accounts/user_confirm_delete.html', {
        'delete_user': user,
        'sessions_count': sessions_count
    })

@login_required
def play(request):
    """Play page."""
    return render(request, 'accounts/play.html')

@login_required
def get_random_accounts(request):
    """Return 3 random gaming accounts as JSON."""
    # Get accounts the user has access to
    if request.user.is_superuser:
        accounts = list(AccountDetail.objects.all())
    else:
        accounts = list(AccountDetail.objects.filter(created_by=request.user))
    
    # Get 3 random accounts (or fewer if not enough exist)
    random_accounts = random.sample(accounts, min(3, len(accounts)))
    
    # Format the data
    data = []
    for acc in random_accounts:
        data.append({
            'id': acc.id,
            'nick': acc.nick,
            'platform': str(acc.platform) if acc.platform else '',
            'phone': acc.phone or '',
            'country': acc.country,
            'withdraw_pass': acc.payment.withdraw_pass if hasattr(acc, 'payment') else '',
            'min_balance': str(acc.payment.min_balance) if hasattr(acc, 'payment') else '0.00',
        })
    
    return JsonResponse({'accounts': data})


@login_required
def eligible_account(request):
    """Return one random eligible account for today, plus a session duration."""
    import json as _json
    from datetime import datetime as _dt
    today = timezone.localdate()
    day_name = today.strftime('%A')
    now_local = timezone.localtime()

    all_accounts = list(AccountDetail.objects.select_related('play_info', 'payment').all())

    # Auto-expire only pending sessions whose 20-min lock has passed
    # (playing/done sessions are only deactivated by explicit user action)
    now_time = now_local.time()
    PlaySession.objects.filter(
        session_date=today, is_active=True, is_pending=True, end_time__lte=now_time
    ).update(is_active=False)

    # Delete stale pending sessions from previous days
    PlaySession.objects.filter(is_pending=True, session_date__lt=today).delete()

    # Active (playing or pending) account IDs — all excluded from selection
    active_ids = set(
        PlaySession.objects.filter(session_date=today, is_active=True).values_list('account_id', flat=True)
    )

    # Client-side excluded IDs (extra safety for same-tab duplicate prevention)
    excluded_param = request.GET.get('excluded', '')
    client_excluded = set()
    if excluded_param:
        for part in excluded_param.split(','):
            try:
                client_excluded.add(int(part))
            except ValueError:
                pass

    excluded_ids = active_ids | client_excluded

    # Total minutes already played today per account (non-pending sessions only)
    today_sessions = PlaySession.objects.filter(
        session_date=today,
        is_pending=False,
        account__in=[a.id for a in all_accounts]
    )
    played_minutes = {}
    for s in today_sessions:
        start_dt = _dt.combine(today, s.start_time)
        end_dt = _dt.combine(today, s.end_time)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        mins = (end_dt - start_dt).total_seconds() / 60
        played_minutes[s.account_id] = played_minutes.get(s.account_id, 0) + mins

    eligible = []  # list of (account, remaining_minutes)
    for acc in all_accounts:
        if acc.id in excluded_ids:
            continue
        if not acc.is_active:
            continue
        try:
            hours = acc.play_info.schedule_of_the_week.get(day_name, -1)
        except Exception:
            continue
        if not hours or hours <= 0:
            continue
        schedule_minutes = hours * 60
        remaining = schedule_minutes - played_minutes.get(acc.id, 0)
        if remaining < 20:  # not enough time left for even a minimum session
            continue
        eligible.append((acc, remaining))

    if not eligible:
        return JsonResponse({'eligible': False})

    acc, remaining_minutes = random.choice(eligible)
    max_duration = min(150, int(remaining_minutes))
    target_median = min(75, (20 + max_duration) / 2)
    duration_minutes = round(gaussian_sample(20, max_duration, target_median))

    account_data = {
        'id': acc.id,
        'nick': acc.nick,
        'device_name': acc.device_name,
        'platform': str(acc.platform) if acc.platform else '',
        'phone': acc.phone or '',
        'withdraw_pass': acc.payment.withdraw_pass if hasattr(acc, 'payment') else '',
        'min_balance': str(acc.payment.min_balance) if hasattr(acc, 'payment') else '0.00',
    }

    # Create pending session in DB immediately — this is the cross-user lock.
    # is_active=True means other users' eligible_account calls will exclude this account.
    # is_pending=True distinguishes it from a real playing session.
    # end_time = now + 20 min (the lock duration).
    # notes stores duration + remaining so active_sessions can restore the pending card.
    lock_end_time = (now_local + timedelta(minutes=20)).time()
    session = PlaySession.objects.create(
        account=acc,
        session_date=today,
        start_time=now_local.time(),
        end_time=lock_end_time,
        created_by=request.user,
        is_active=True,
        is_pending=True,
        notes=_json.dumps({'d': duration_minutes, 'r': round(remaining_minutes)}),
    )

    return JsonResponse({
        'eligible': True,
        'account': account_data,
        'remaining_minutes': round(remaining_minutes),
        'duration_minutes': duration_minutes,
        'expires_in_seconds': 1200,
        'session_id': session.id,
    })


@login_required
def start_session_play(request):
    """Activate a pending PlaySession — updates its times and clears the pending flag."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    data = json.loads(request.body)
    session_id = data.get('session_id')
    duration_minutes = int(data.get('duration_minutes', 60))

    session = get_object_or_404(PlaySession, pk=session_id, is_pending=True, created_by=request.user)

    now_local = timezone.localtime()
    start_time = now_local.time().replace(microsecond=0)
    end_time = (now_local + timedelta(minutes=duration_minutes)).time().replace(microsecond=0)

    session.is_pending = False
    session.start_time = start_time
    session.end_time = end_time
    session.save(update_fields=['is_pending', 'start_time', 'end_time'])

    return JsonResponse({
        'session_id': session.id,
        'end_time': end_time.strftime('%H:%M'),
    })


@login_required
def active_sessions(request):
    """Return all currently active sessions for today so the client can restore cards on page load."""
    import json as _json
    from datetime import datetime as _dt
    today = timezone.localdate()
    now_local = timezone.localtime()
    now_naive = now_local.replace(tzinfo=None)

    # Playing: superusers monitor all users' sessions; others see own only
    if request.user.is_superuser:
        playing_qs = PlaySession.objects.filter(
            session_date=today, is_active=True, is_pending=False, is_done=False
        ).select_related('account', 'account__payment', 'created_by')
    else:
        playing_qs = PlaySession.objects.filter(
            session_date=today, is_active=True, is_pending=False, is_done=False,
            created_by=request.user
        ).select_related('account', 'account__payment')

    # Pending and done are always the current user's own sessions
    own_qs = PlaySession.objects.filter(
        session_date=today, is_active=True, created_by=request.user
    ).select_related('account', 'account__payment')
    pending_qs = own_qs.filter(is_pending=True)
    done_qs = own_qs.filter(is_pending=False, is_done=True)

    result = []
    for s in playing_qs:
        start_dt = _dt.combine(today, s.start_time)
        end_dt = _dt.combine(today, s.end_time)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)

        if s.paused and s.pause_time:
            pause_local = timezone.localtime(s.pause_time).replace(tzinfo=None)
            seconds_left = int((end_dt - pause_local).total_seconds())
        else:
            seconds_left = int((end_dt - now_naive).total_seconds())

        timed_out = seconds_left <= 0
        if timed_out:
            seconds_left = 0
        try:
            meta = _json.loads(s.notes or '{}')
            remaining_after = max(0, int(meta.get('r', 0)) - int(meta.get('d', 0)))
        except Exception:
            remaining_after = 0
        acc = s.account
        result.append({
            'session_id': s.id,
            'seconds_left': seconds_left,
            'timed_out': timed_out,
            'remaining_after': remaining_after,
            'end_time': s.end_time.strftime('%H:%M'),
            'paused': s.paused,
            'created_by': s.created_by.username if s.created_by else None,
            'account': {
                'id': acc.id,
                'nick': acc.nick,
                'device_name': acc.device_name,
                'platform': str(acc.platform) if acc.platform else '',
                'phone': acc.phone or '',
                'withdraw_pass': acc.payment.withdraw_pass if hasattr(acc, 'payment') else '',
                'min_balance': str(acc.payment.min_balance) if hasattr(acc, 'payment') else '0.00',
            },
        })

    done_result = []
    for s in done_qs:
        try:
            meta = _json.loads(s.notes or '{}')
            r = int(meta.get('r', 0))
        except Exception:
            r = 0
        start_dt = _dt.combine(today, s.start_time)
        end_dt = _dt.combine(today, s.end_time)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        actual_minutes = int((end_dt - start_dt).total_seconds() / 60)
        remaining_after = max(0, r - actual_minutes)
        acc = s.account
        done_result.append({
            'session_id': s.id,
            'remaining_after': remaining_after,
            'created_by': s.created_by.username if s.created_by else None,
            'account': {
                'id': acc.id,
                'nick': acc.nick,
                'device_name': acc.device_name,
                'platform': str(acc.platform) if acc.platform else '',
                'phone': acc.phone or '',
                'withdraw_pass': acc.payment.withdraw_pass if hasattr(acc, 'payment') else '',
                'min_balance': str(acc.payment.min_balance) if hasattr(acc, 'payment') else '0.00',
            },
        })

    pending_result = []
    for s in pending_qs:
        end_dt = _dt.combine(today, s.end_time)
        expires_in = int((end_dt - now_naive).total_seconds())
        if expires_in <= 0:
            s.is_active = False
            s.save(update_fields=['is_active'])
            continue
        try:
            meta = _json.loads(s.notes or '{}')
            duration_minutes = meta.get('d', 60)
            remaining_minutes = meta.get('r', 0)
        except (ValueError, TypeError):
            duration_minutes, remaining_minutes = 60, 0
        acc = s.account
        pending_result.append({
            'session_id': s.id,
            'expires_in_seconds': expires_in,
            'duration_minutes': duration_minutes,
            'remaining_minutes': remaining_minutes,
            'account': {
                'id': acc.id,
                'nick': acc.nick,
                'device_name': acc.device_name,
                'platform': str(acc.platform) if acc.platform else '',
                'phone': acc.phone or '',
                'withdraw_pass': acc.payment.withdraw_pass if hasattr(acc, 'payment') else '',
                'min_balance': str(acc.payment.min_balance) if hasattr(acc, 'payment') else '0.00',
            },
        })

    return JsonResponse({'sessions': result, 'done': done_result, 'pending': pending_result})


@login_required
def cancel_pending_session(request):
    """Delete a pending PlaySession so the account becomes available again immediately."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    data = json.loads(request.body)
    session_id = data.get('session_id')

    PlaySession.objects.filter(pk=session_id, is_pending=True, created_by=request.user).delete()
    return JsonResponse({'ok': True})


@login_required
def dismiss_session(request):
    """Mark a done session as inactive so it leaves the play page."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    data = json.loads(request.body)
    session_id = data.get('session_id')

    PlaySession.objects.filter(pk=session_id, is_done=True, created_by=request.user).update(is_active=False)
    return JsonResponse({'ok': True})


@login_required
def finish_session_play(request):
    """Mark a session as no longer active."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    data = json.loads(request.body)
    session_id = data.get('session_id')

    session = get_object_or_404(PlaySession, pk=session_id)
    session.is_active = False
    session.save(update_fields=['is_active'])

    return JsonResponse({'ok': True})


@login_required
def pause_session_play(request):
    """Pause an active session."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    data = json.loads(request.body)
    session_id = data.get('session_id')

    session = get_object_or_404(PlaySession, pk=session_id)
    session.paused = True
    session.pause_time = timezone.now()
    session.save(update_fields=['paused', 'pause_time'])

    return JsonResponse({'ok': True})


@login_required
def resume_session_play(request):
    """Resume a paused session by extending end_time."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    data = json.loads(request.body)
    session_id = data.get('session_id')

    session = get_object_or_404(PlaySession, pk=session_id)

    if session.paused and session.pause_time:
        # Calculate how long it was paused
        paused_duration = timezone.now() - session.pause_time
        paused_minutes = int(paused_duration.total_seconds() / 60)

        # Extend end_time by the paused duration
        from datetime import datetime, timedelta
        today = session.session_date
        current_end = datetime.combine(today, session.end_time)
        new_end = current_end + timedelta(minutes=paused_minutes)
        session.end_time = new_end.time()

        # Clear pause state
        session.paused = False
        session.pause_time = None
        session.save(update_fields=['paused', 'pause_time', 'end_time'])

        # Return remaining seconds for the frontend timer
        now_local = timezone.localtime()
        new_end_dt = datetime.combine(today, session.end_time)
        if new_end_dt <= datetime.combine(today, session.start_time):
            new_end_dt = datetime.combine(today + timedelta(days=1), session.end_time)
        seconds_left = int((new_end_dt - now_local.replace(tzinfo=None)).total_seconds())

        return JsonResponse({'ok': True, 'seconds_left': seconds_left})

    return JsonResponse({'error': 'Session not paused'}, status=400)


@login_required
def stop_session(request):
    """Stop an active session early (user manually ends it before timer finishes)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    data = json.loads(request.body)
    session_id = data.get('session_id')

    session = get_object_or_404(PlaySession, pk=session_id)

    import json as _json
    from datetime import datetime as _dt
    now_local = timezone.localtime()
    today = timezone.localdate()
    actual_stop_time = now_local.time().replace(microsecond=0)

    start_dt = _dt.combine(today, session.start_time)
    stop_dt = _dt.combine(today, actual_stop_time)
    if stop_dt < start_dt:
        stop_dt += timedelta(days=1)
    actual_minutes = int((stop_dt - start_dt).total_seconds() / 60)

    try:
        meta = _json.loads(session.notes or '{}')
        r = int(meta.get('r', 0))
    except Exception:
        r = 0
    remaining_after = max(0, r - actual_minutes)

    session.end_time = actual_stop_time
    session.is_done = True
    session.paused = False
    session.save(update_fields=['end_time', 'is_done', 'paused'])

    return JsonResponse({'ok': True, 'remaining_after': remaining_after})


@login_required
def account_search(request):
    """Search accounts by nickname or API key for autocomplete."""
    q = request.GET.get('q', '').strip()
    if len(q) < 1:
        return JsonResponse({'results': []})

    qs = AccountDetail.objects.select_related('platform')
    if not request.user.is_superuser:
        qs = qs.filter(play_sessions__created_by=request.user).distinct()

    # Search by nick OR by API (left outer join via isnull handles missing Security)
    qs = qs.filter(Q(nick__icontains=q) | Q(security__api__icontains=q))[:10]

    results = []
    for acc in qs:
        api_key = ''
        try:
            api_key = acc.security.api or ''
        except Security.DoesNotExist:
            pass
        results.append({
            'id': acc.id,
            'nick': acc.nick,
            'platform': str(acc.platform) if acc.platform else '',
            'api': api_key,
        })

    return JsonResponse({'results': results})


@login_required
def deposit_withdrawal(request):
    """Deposit/Withdrawal page — form with search bar."""
    return render(request, 'accounts/deposit_withdrawal.html')


@login_required
def deposit_withdrawal_create(request):
    """Create a deposit or withdrawal entry."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    import json
    data = json.loads(request.body)
    account_id = data.get('account_id')
    deposit = data.get('deposit')
    withdrawal = data.get('withdrawal')

    if not account_id:
        return JsonResponse({'error': 'Account is required'}, status=400)
    if not deposit and not withdrawal:
        return JsonResponse({'error': 'Enter a deposit or withdrawal amount'}, status=400)

    account = get_object_or_404(AccountDetail, pk=account_id)

    entry = DepositWithdrawal.objects.create(
        account=account,
        deposit=deposit if deposit else None,
        withdrawal=withdrawal if withdrawal else None,
        created_by=request.user,
    )

    return JsonResponse({
        'id': entry.id,
        'account': account.nick,
        'platform': str(account.platform) if account.platform else '',
        'deposit': str(entry.deposit) if entry.deposit else None,
        'withdrawal': str(entry.withdrawal) if entry.withdrawal else None,
        'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M'),
    })


@login_required
@user_passes_test(is_superuser)
def deposit_withdrawal_reports(request):
    """Reports page — superuser only."""
    return render(request, 'accounts/deposit_withdrawal_reports.html')


@login_required
@user_passes_test(is_superuser)
def deposit_withdrawal_history(request):
    """Return deposit/withdrawal history as JSON, with optional filters."""
    q = request.GET.get('q', '').strip()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    qs = DepositWithdrawal.objects.select_related('account', 'account__platform')

    if q:
        qs = qs.filter(
            Q(account__nick__icontains=q) | Q(account__security__api__icontains=q)
        )
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    # Totals from the same filtered queryset
    totals = qs.aggregate(
        total_deposits=Sum('deposit'),
        total_withdrawals=Sum('withdrawal'),
    )

    entries = []
    for e in qs:
        entries.append({
            'id': e.id,
            'account': e.account.nick,
            'platform': str(e.account.platform) if e.account.platform else '',
            'deposit': str(e.deposit) if e.deposit else None,
            'withdrawal': str(e.withdrawal) if e.withdrawal else None,
            'created_at': e.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({
        'entries': entries,
        'totals': {
            'deposits': str(totals['total_deposits'] or 0),
            'withdrawals': str(totals['total_withdrawals'] or 0),
        }
    })


def service_worker_js(request):
    js = """
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(function(clientList) {
            for (var i = 0; i < clientList.length; i++) {
                if (clientList[i].url.indexOf('/play') !== -1 && 'focus' in clientList[i]) {
                    return clientList[i].focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow('/play/');
            }
        })
    );
});

self.addEventListener('message', function(event) {
    if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
        self.registration.showNotification(event.data.title || 'Session Complete', {
            body: event.data.body || 'A play session has finished!',
            icon: '/static/favicon.ico',
            requireInteraction: true,
            tag: 'session-done-' + (event.data.tag || Date.now()),
        });
    }
});
"""
    return HttpResponse(js, content_type='application/javascript')
