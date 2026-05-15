import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Address, Order


def validate_postal_code(value):
    if not re.match(r'^[a-zA-Z0-9\s\-]{3,10}$', value):
        raise ValidationError('Enter a valid postal code.')


def validate_phone(value):
    if value and not re.match(r'^\+?[\d\s\-()]{7,20}$', value):
        raise ValidationError('Enter a valid phone number.')


def validate_card_number(value):
    cleaned = value.replace(' ', '').replace('-', '')
    if not cleaned.isdigit():
        raise ValidationError('Card number must contain only digits.')
    if len(cleaned) < 13 or len(cleaned) > 19:
        raise ValidationError('Invalid card number length.')
    if not luhn_check(cleaned):
        raise ValidationError('Invalid card number.')


def validate_expiry(value):
    if not re.match(r'^(0[1-9]|1[0-2])\/([0-9]{2})$', value):
        raise ValidationError('Expiry must be in MM/YY format.')
    month, year = value.split('/')
    from datetime import datetime
    import calendar
    exp_date = datetime(2000 + int(year), int(month), calendar.monthrange(2000 + int(year), int(month))[1])
    if exp_date < datetime.now():
        raise ValidationError('Card has expired.')


def validate_cvv(value):
    if not re.match(r'^[0-9]{3,4}$', value):
        raise ValidationError('CVV must be 3 or 4 digits.')


def luhn_check(card_number):
    total = 0
    reverse_digits = card_number[::-1]
    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


class AddressForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'John Doe',
        })
    )
    line1 = forms.CharField(
        max_length=255,
        label='Address Line 1',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': '123 Main Street',
        })
    )
    line2 = forms.CharField(
        max_length=255,
        required=False,
        label='Address Line 2 (Optional)',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'Apt 4B, Suite 100',
        })
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'New York',
        })
    )
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'NY',
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        validators=[validate_postal_code],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': '10001',
        })
    )
    country = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'United States',
        })
    )
    phone = forms.CharField(
        max_length=30,
        required=False,
        validators=[validate_phone],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': '+1 (555) 000-0000',
        })
    )
    is_default = forms.BooleanField(
        required=False,
        label='Set as default address',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-primary border-gray-300 rounded focus:ring-primary',
        })
    )

    class Meta:
        model = Address
        fields = ('full_name', 'line1', 'line2', 'city', 'state', 'postal_code', 'country', 'phone', 'is_default')

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name')
        if len(name.strip()) < 2:
            raise ValidationError('Full name must be at least 2 characters long.')
        return name.strip()

    def clean_line1(self):
        line1 = self.cleaned_data.get('line1')
        if len(line1.strip()) < 3:
            raise ValidationError('Please enter a valid address.')
        return line1.strip()

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if len(city.strip()) < 2:
            raise ValidationError('Please enter a valid city.')
        return city.strip()

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if len(country.strip()) < 2:
            raise ValidationError('Please enter a valid country.')
        return country.strip()

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user:
            instance.user = user
        if instance.is_default:
            Address.objects.filter(user=user, is_default=True).update(is_default=False)
        if commit:
            instance.save()
        return instance


class CheckoutForm(forms.Form):
    PAYMENT_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('credit_card', 'Credit/Debit Card'),
        ('paypal', 'PayPal'),
        ('razorpay', 'Razorpay'),
    ]

    address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        widget=forms.RadioSelect(attrs={
            'class': 'text-primary',
        }),
        label='Shipping Address',
        error_messages={'required': 'Please select a shipping address.'},
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'text-primary',
        }),
        initial='cash_on_delivery',
    )
    card_number = forms.CharField(
        max_length=19,
        required=False,
        validators=[validate_card_number],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': '1234 5678 9012 3456',
        })
    )
    expiry = forms.CharField(
        max_length=5,
        required=False,
        validators=[validate_expiry],
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': 'MM/YY',
        })
    )
    cvv = forms.CharField(
        max_length=4,
        required=False,
        validators=[validate_cvv],
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary transition',
            'placeholder': '123',
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['address'].queryset = Address.objects.filter(user=user)

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        if payment_method in ('credit_card', 'stripe'):
            card_number = cleaned_data.get('card_number')
            expiry = cleaned_data.get('expiry')
            cvv = cleaned_data.get('cvv')
            if not card_number:
                self.add_error('card_number', 'Card number is required.')
            if not expiry:
                self.add_error('expiry', 'Expiry date is required.')
            if not cvv:
                self.add_error('cvv', 'CVV is required.')
        return cleaned_data
