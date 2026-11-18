"""Registration/login forms — phone-as-username (database-design.md §5.1).

Phone numbers are stored normalized to E.164 (+254…) per SRS 5.3; a small
normalizer handles common local formats like 07xx / 2547xx.
"""

import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

PHONE_RE = re.compile(r'^\+?[0-9]{9,15}$')


def normalize_phone(raw):
    """Normalize a Kenyan phone number to E.164 (+254…)."""
    digits = re.sub(r'[\s\-()+]', '', raw or '')
    if digits.startswith('00'):
        digits = digits[2:]
    if digits.startswith('0') and len(digits) == 10:  # 0712 345 678
        digits = '254' + digits[1:]
    if not digits.startswith('+'):
        digits = '+' + digits
    if not PHONE_RE.match(digits):
        raise forms.ValidationError('Enter a valid phone number.')
    return digits


class FarmerRegistrationForm(forms.Form):
    name = forms.CharField(max_length=120)
    phone_number = forms.CharField(max_length=20)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_phone_number(self):
        phone = normalize_phone(self.cleaned_data['phone_number'])
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('This phone number is already registered.')
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            self.add_error('password2', 'Passwords do not match.')
        else:
            validate_password(cleaned.get('password1'))
        return cleaned

    def save(self):
        return User.objects.create_user(
            phone_number=self.cleaned_data['phone_number'],
            password=self.cleaned_data['password1'],
            name=self.cleaned_data['name'],
            role=User.Role.FARMER,
        )
