from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    AccountDetail, Payment, PlaySession, Platform,
    ProxyVpn, WalletProvider, Network,
    Location, Security, PlayInfo, LastTransaction,
    Deposit, Withdrawal, TaskLog, Disciplines, Expense, UserProfile,
)


def _is_system_admin(user):
    return user.is_superuser and getattr(getattr(user, 'profile', None), 'is_system_admin', False)


# Protect user management — only system admins (CLI-created) can modify users
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    def has_add_permission(self, request):
        return _is_system_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_system_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_system_admin(request.user)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_system_admin']

    def has_add_permission(self, request):
        return _is_system_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_system_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_system_admin(request.user)


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(ProxyVpn)
class ProxyVpnAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(WalletProvider)
class WalletProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Disciplines)
class DisciplinesAdmin(admin.ModelAdmin):
    list_display = ['discipline', 'platform', 'created_at']
    search_fields = ['discipline']
    list_filter = ['platform']


@admin.register(AccountDetail)
class AccountDetailAdmin(admin.ModelAdmin):
    list_display = ['nick', 'platform', 'email', 'phone', 'created_at']
    search_fields = ['nick', 'email', 'phone']
    list_filter = ['platform', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['account', 'country', 'ip', 'proxy_vpn']
    search_fields = ['account__nick', 'ip', 'country']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Security)
class SecurityAdmin(admin.ModelAdmin):
    list_display = ['account', 'login', 'app_id']
    search_fields = ['account__nick', 'login']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PlayInfo)
class PlayInfoAdmin(admin.ModelAdmin):
    list_display = ['account', 'play_days_per_week', 'holiday_days_per_year', 'updated_at']
    search_fields = ['account__nick']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LastTransaction)
class LastTransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'txid', 'network', 'wallet', 'time', 'first_withdraw']
    search_fields = ['account__nick', 'txid', 'wallet']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['account', 'min_balance', 'wallet_provider', 'created_at']
    search_fields = ['account__nick', 'account__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PlaySession)
class PlaySessionAdmin(admin.ModelAdmin):
    list_display = ['account', 'session_date', 'start_time', 'end_time', 'duration_display_admin', 'is_active', 'paused', 'created_by', 'created_at']
    list_filter = ['session_date', 'is_active', 'paused', 'created_by']
    search_fields = ['account__nick', 'account__email']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    date_hierarchy = 'session_date'

    def duration_display_admin(self, obj):
        return obj.duration_display
    duration_display_admin.short_description = 'Duration'

    def get_queryset(self, request):
        if request.user.is_superuser:
            return PlaySession.objects.all_including_old()
        return super().get_queryset(request).filter(created_by=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        return obj.created_by == request.user

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        return obj.created_by == request.user


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ['account', 'amount', 'network', 'wallet', 'current_balance', 'created_by', 'created_at']
    list_filter = ['network', 'created_by', 'created_at']
    search_fields = ['account__nick']
    readonly_fields = ['created_at']


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['account', 'amount', 'network', 'wallet', 'current_balance', 'created_by', 'created_at']
    list_filter = ['network', 'created_by', 'created_at']
    search_fields = ['account__nick']
    readonly_fields = ['created_at']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense', 'amount', 'created_by', 'created_at']
    list_filter = ['created_by', 'created_at']
    search_fields = ['expense']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'success', 'ran_at']
    list_filter = ['success', 'task_name']
    readonly_fields = ['task_name', 'ran_at', 'success', 'detail']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
