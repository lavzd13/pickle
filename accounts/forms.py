from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import PlaySession, AccountDetail, Payment, WalletProvider, LastTransaction, Location, Security, Disciplines


class PlaySessionForm(forms.ModelForm):
    class Meta:
        model = PlaySession
        fields = ['account', 'session_date', 'start_time', 'end_time', 'notes']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-control'}),
            'session_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TextInput(attrs={'class': 'form-control timepicker', 'placeholder': 'HH:MM'}),
            'end_time': forms.TextInput(attrs={'class': 'form-control timepicker', 'placeholder': 'HH:MM'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DaySessionForm(forms.ModelForm):
    """Form for editing sessions within a single day (account+date are set by the view)."""
    class Meta:
        model = PlaySession
        fields = ['start_time', 'end_time', 'notes']
        widgets = {
            'start_time': forms.TextInput(attrs={'class': 'form-control timepicker', 'placeholder': 'HH:MM'}),
            'end_time': forms.TextInput(attrs={'class': 'form-control timepicker', 'placeholder': 'HH:MM'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional notes'}),
        }


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['country', 'ip', 'proxy_vpn', 'latitude', 'longtitude']
        widgets = {
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'ip': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.TextInput(attrs={'class': 'form-control'}),
            'longtitude': forms.TextInput(attrs={'class': 'form-control'}),
            'proxy_vpn': forms.Select(attrs={'class': 'form-control'}),
		}
        
class SecurityForm(forms.ModelForm):
    class Meta:
        model = Security
        fields = ['app_id', 'login', 'login_pass', 'api']
        widgets = {
            'app_id': forms.TextInput(attrs={'class': 'form-control'}),
            'login': forms.TextInput(attrs={'class': 'form-control'}),
            'login_pass': forms.TextInput(attrs={'class': 'form-control'}),
            'api': forms.TextInput(attrs={'class': 'form-control'}),
		}

class AccountDetailForm(forms.ModelForm):
    ACCOUNT_STATUS_CHOICES = [
        ('is_new', 'New'),
        ('is_active', 'Active'),
        ('is_active_no_schedule', 'Active / No Schedule'),
        ('is_inactive', 'Inactive'),
        ('is_banned', 'Banned'),
    ]
    account_status = forms.ChoiceField(
        choices=ACCOUNT_STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='is_new',
        label='Account Status',
    )

    class Meta:
        model = AccountDetail
        fields = ['nick', 'device_name', 'email', 'platform', 'discipline', 'phone', 'related_to', 'creation_date']
        widgets = {
            'nick': forms.TextInput(attrs={'class': 'form-control'}),
            'device_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'platform': forms.Select(attrs={'class': 'form-control'}),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'related_to': forms.HiddenInput(),
            'creation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter disciplines to the selected platform (or empty for new accounts)
        if self.instance and self.instance.pk and self.instance.platform_id:
            self.fields['discipline'].queryset = Disciplines.objects.filter(platform=self.instance.platform)
        else:
            self.fields['discipline'].queryset = Disciplines.objects.none()
        # related_to: only show accounts that are not themselves related to another (potential main accounts)
        related_qs = AccountDetail.objects.filter(related_to__isnull=True)
        if self.instance and self.instance.pk:
            related_qs = related_qs.exclude(pk=self.instance.pk)
        self.fields['related_to'].queryset = related_qs
        self.fields['related_to'].required = False
        if not self.instance.pk and not self.initial.get('creation_date'):
            self.fields['creation_date'].initial = timezone.localdate()
        if self.instance and self.instance.pk:
            if self.instance.is_active:
                self.fields['account_status'].initial = 'is_active'
            elif self.instance.is_active_no_schedule:
                self.fields['account_status'].initial = 'is_active_no_schedule'
            elif self.instance.is_inactive:
                self.fields['account_status'].initial = 'is_inactive'
            elif self.instance.is_banned:
                self.fields['account_status'].initial = 'is_banned'
            else:
                self.fields['account_status'].initial = 'is_new'

    def save(self, commit=True):
        instance = super().save(commit=False)
        status = self.cleaned_data.get('account_status', 'is_new')
        instance.is_new = (status == 'is_new')
        instance.is_active = (status == 'is_active')
        instance.is_active_no_schedule = (status == 'is_active_no_schedule')
        instance.is_inactive = (status == 'is_inactive')
        instance.is_banned = (status == 'is_banned')
        if commit:
            instance.save()
        return instance
        

class LastTransactionForm(forms.ModelForm):
    class Meta:
        model = LastTransaction
        fields = ['txid', 'network', 'wallet', 'time', 'picture', 'first_withdraw']
        widgets = {
            'txid': forms.TextInput(attrs={'class': 'form-control'}),
            'wallet': forms.TextInput(attrs={'class': 'form-control'}),
            'time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'network': forms.Select(attrs={'class': 'form-control'}),
            'picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'first_withdraw': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class WalletProviderForm(forms.ModelForm):
    class Meta:
        model = WalletProvider
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Wallet provider name'})
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['withdraw_pass', 'min_balance', 'crypto_wallet', 'wallet_provider', 'network']
        widgets = {
            'withdraw_pass': forms.NumberInput(attrs={'class': 'form-control'}),
            'crypto_wallet': forms.TextInput(attrs={'class': 'form-control'}),
            'min_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'wallet_provider': forms.Select(attrs={'class': 'form-control'}),
            'network': forms.Select(attrs={'class': 'form-control'}),
        }


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Enter a strong password"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            #'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data


class UserEditForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Leave blank to keep current password"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        label="Confirm Password"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data
