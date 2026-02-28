from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from django.conf import settings

class Platform(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platforms'
        ordering = ['name']
    def __str__(self):
        return self.name
    
class ProxyVpn(models.Model):
    name = models.CharField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'proxy_vpn'
        ordering = ['name']
    def __str__(self):
        return self.name

class WalletProvider(models.Model):
    """Wallet providers"""
    name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallet_provider'
        ordering = ['name']
    def __str__(self):
        return self.name

class Network(models.Model):
    """Blockchain networks"""
    name = models.CharField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'network'
        ordering = ['name']
    def __str__(self):
        return self.name


class AccountDetail(models.Model):
    """Account details model - represents a gaming account (not a login user)"""
    nick = models.CharField(max_length=100)
    device_name = models.CharField(max_length=100, blank=True)
    platform = models.ForeignKey(Platform, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_new = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_active_no_schedule = models.BooleanField(default=False)
    is_inactive = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    creation_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'acc_details'
        verbose_name = 'Account Detail'
        verbose_name_plural = 'Account Details'
        constraints = [
            # nick + platform is always enforced
            models.UniqueConstraint(
                fields=['nick', 'platform'],
                name='unique_nick_platform'
            ),
            # email + platform only when email is not blank
            models.UniqueConstraint(
                fields=['email', 'platform'],
                condition=Q(email__gt=''),
                name='unique_email_platform'
            ),
            # phone + platform only when phone is not blank/null
            models.UniqueConstraint(
                fields=['phone', 'platform'],
                condition=Q(phone__isnull=False) & Q(phone__gt=''),
                name='unique_phone_platform'
            ),
        ]

    def clean(self):
        """Validate unique combinations before saving for user-friendly errors."""
        qs = AccountDetail.objects.filter(platform=self.platform)
        if self.pk:
            qs = qs.exclude(pk=self.pk)

        if qs.filter(nick=self.nick).exists():
            raise ValidationError({'nick': 'An account with this nickname already exists on this platform.'})

        if self.email and qs.filter(email=self.email).exists():
            raise ValidationError({'email': 'An account with this email already exists on this platform.'})

        if self.phone and qs.filter(phone=self.phone).exists():
            raise ValidationError({'phone': 'An account with this phone already exists on this platform.'})

    def __str__(self):
        return f"{self.nick} ({self.platform})"

class Location(models.Model):
    account = models.OneToOneField(AccountDetail, on_delete=models.CASCADE, related_name='location')
    country = models.CharField(blank=True)
    ip = models.CharField(blank=True)
    proxy_vpn = models.ForeignKey(ProxyVpn, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.CharField(blank=True)
    longtitude = models.CharField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'location'

class Security(models.Model):
    account = models.OneToOneField(AccountDetail, on_delete=models.CASCADE, related_name='security')
    app_id = models.CharField(blank=True)
    login = models.CharField(blank=True)
    login_pass = models.CharField(blank=True)
    api = models.CharField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'security'

def default_schedule():
    return {
        "Monday": -1,
        "Tuesday": -1,
        "Wednesday": -1,
        "Thursday": -1,
        "Friday": -1,
        "Saturday": -1,
        "Sunday": -1,
    }

class PlayInfo(models.Model):
    """Account playing info"""
    DAYS_OF_THE_WEEK = 7
    account = models.OneToOneField(AccountDetail, on_delete=models.CASCADE, related_name='play_info')
    holiday_days_per_year = models.FloatField(blank=False)
    play_days_per_week = models.FloatField(blank=False)
    hours_per_day = models.FloatField(blank=True)
    schedule_of_the_week = models.JSONField(default=default_schedule)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'play_info'

class LastTransaction(models.Model):
    """Last transcation info"""
    account = models.OneToOneField(AccountDetail, on_delete=models.CASCADE, related_name='last_transaction')
    picture = models.ImageField(upload_to='transactions/', blank=True)
    txid = models.CharField(blank=True)
    network = models.ForeignKey(Network, on_delete=models.SET_NULL, null=True, blank=True)
    wallet = models.CharField(blank=True)
    time = models.DateTimeField(blank=True, null=True)
    first_withdraw = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'last_transaction'

class Payment(models.Model):
    """Payment information model"""
    account = models.OneToOneField(AccountDetail, on_delete=models.CASCADE, related_name='payment')
    withdraw_pass = models.CharField(help_text="Withdrawal password", blank=True)
    min_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    crypto_wallet = models.CharField(blank=True)
    wallet_provider = models.ForeignKey(WalletProvider, on_delete=models.SET_NULL, null=True, blank=True)
    network = models.ForeignKey(Network, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment'
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment for {self.account.nick}"


class PlaySessionManager(models.Manager):
    """Custom manager for PlaySession with retention policy"""
    
    def get_queryset(self):
        """Override to exclude sessions older than retention period"""
        retention_days = getattr(settings, 'SESSION_RETENTION_DAYS', 60)
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        return super().get_queryset().filter(session_date__gte=cutoff_date)
    
    def all_including_old(self):
        """Get all sessions including those beyond retention period (superuser only)"""
        return super().get_queryset()


class PlaySession(models.Model):
    """Play sessions model - tracks gaming activity with exact start/end times"""
    account = models.ForeignKey(AccountDetail, on_delete=models.CASCADE, related_name='play_sessions')
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_pending = models.BooleanField(default=False)
    is_done = models.BooleanField(default=False)
    paused = models.BooleanField(default=False)
    pause_time = models.DateTimeField(null=True, blank=True)
    break_until = models.DateTimeField(null=True, blank=True)

    objects = PlaySessionManager()

    class Meta:
        db_table = 'play_sessions'
        verbose_name = 'Play Session'
        verbose_name_plural = 'Play Sessions'
        unique_together = ['account', 'session_date', 'start_time']
        ordering = ['-session_date', '-start_time']
        indexes = [
            models.Index(fields=['session_date']),
            models.Index(fields=['account', 'session_date']),
        ]

    @property
    def duration(self):
        """Return duration as a timedelta. Handles cross-midnight sessions."""
        start_dt = datetime.combine(self.session_date, self.start_time)
        end_dt = datetime.combine(self.session_date, self.end_time)
        if end_dt < start_dt:
            # Session crossed midnight
            end_dt += timedelta(days=1)
        elif end_dt == start_dt:
            # Started and stopped in same minute - count as 1 minute
            return timedelta(minutes=1)
        return end_dt - start_dt

    @property
    def duration_display(self):
        """Return duration as a human-readable string like '2h 30m'."""
        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours and minutes:
            return f"{hours}h {minutes}m"
        elif hours:
            return f"{hours}h"
        return f"{minutes}m"

    def __str__(self):
        return f"{self.account.nick} - {self.session_date} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    def is_editable_by(self, user):
        """Check if user can edit this session"""
        if user.is_superuser:
            return True
        return self.created_by == user

DW_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


class Deposit(models.Model):
    account = models.ForeignKey(AccountDetail, on_delete=models.CASCADE, related_name='deposits')
    network = models.ForeignKey(Network, on_delete=models.SET_NULL, null=True, blank=True)
    wallet_name = models.CharField(blank=True, default='')
    wallet = models.CharField(blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=DW_STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deposits')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'deposit'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account.nick} +{self.amount}"


class Withdrawal(models.Model):
    account = models.ForeignKey(AccountDetail, on_delete=models.CASCADE, related_name='withdrawals')
    network = models.ForeignKey(Network, on_delete=models.SET_NULL, null=True, blank=True)
    wallet_name = models.CharField(blank=True, default='')
    wallet = models.CharField(blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=DW_STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='withdrawals')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'withdrawal'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account.nick} -{self.amount}"


class DepositOrder(models.Model):
    """Order submitted by a regular user — to be forwarded to the Telegram bot."""
    account = models.ForeignKey(AccountDetail, on_delete=models.CASCADE, related_name='deposit_orders')
    network = models.ForeignKey(Network, on_delete=models.SET_NULL, null=True, blank=True)
    wallet_address = models.CharField(blank=True, default='')
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deposit_orders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'deposit_order'
        ordering = ['-created_at']

    def __str__(self):
        return f"DepositOrder {self.account.nick}"


class WithdrawalOrder(models.Model):
    """Order submitted by a regular user — to be forwarded to the Telegram bot."""
    account = models.ForeignKey(AccountDetail, on_delete=models.CASCADE, related_name='withdrawal_orders')
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='withdrawal_orders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'withdrawal_order'
        ordering = ['-created_at']

    def __str__(self):
        return f"WithdrawalOrder {self.account.nick}"

class SMSPlatform(models.Model):
    """Global list of SMS platforms available for selection"""
    name = models.CharField(blank=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sms_platforms')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sms_platform'
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"


class CountryBlackList(models.Model):
    """Countries which are on blacklist because of SMS not arriving on grizzly"""
    country = models.CharField(blank=True)
    platforms = models.ManyToManyField(SMSPlatform, blank=True, related_name='countries')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='country_blacklist')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'country_blacklist'

    def __str__(self):
        return f"{self.country}"


class TaskLog(models.Model):
    task_name = models.CharField(max_length=200)
    ran_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    detail = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'task_log'
        ordering = ['-ran_at']

    def __str__(self):
        status = 'OK' if self.success else 'FAIL'
        return f"[{status}] {self.task_name} @ {self.ran_at:%Y-%m-%d %H:%M}"
