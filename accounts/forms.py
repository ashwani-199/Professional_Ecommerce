import re
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import User


def validate_phone(value):
    if value and not re.match(r'^\+?[\d\s\-()]{7,20}$', value):
        raise ValidationError('Enter a valid phone number (7-20 digits, optional + prefix).')


def validate_username(value):
    if not re.match(r'^[a-zA-Z0-9_]+$', value):
        raise ValidationError('Username can only contain letters, numbers, and underscores.')
    if len(value) < 3:
        raise ValidationError('Username must be at least 3 characters long.')


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'you@example.com',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[validate_phone],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': '+1 (555) 000-0000',
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'johndoe',
        })
        self.fields['username'].validators.append(validate_username)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError('Username must be at least 3 characters long.')
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password and len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if password and password.isdigit():
            raise ValidationError('Password cannot be entirely numeric.')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'Enter your username',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        if not self.user_cache:
            raise forms.ValidationError(
                'Invalid username or password. Please try again.',
                code='invalid_login',
            )
        if not self.user_cache.is_active:
            raise forms.ValidationError(
                'This account has been deactivated. Please contact support.',
                code='inactive',
            )
        return cleaned_data


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'you@example.com',
        })
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email=email).exists():
            raise ValidationError('No account found with this email address.')
        return email


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'autocomplete': 'new-password',
        })
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'autocomplete': 'new-password',
        })
    )


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'autocomplete': 'current-password',
        })
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'autocomplete': 'new-password',
        })
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'autocomplete': 'new-password',
        })
    )


class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[validate_phone],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
        })
    )

    class Meta:
        model = User
        fields = ('email', 'phone', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ('first_name', 'last_name'):
            self.fields[field].widget.attrs.update({
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This email address is already registered.')
        return email
