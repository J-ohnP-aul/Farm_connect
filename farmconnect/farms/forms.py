"""Farm profile form — FR-05..FR-10.

Location is captured as lat/lng text fields and converted to a Point;
`show_exact_pin` implements the privacy opt-in (FR-08/09). `is_active` is
NOT in this form — only an admin activates a farm (curated pilot).
"""

from django import forms
from django.contrib.gis.geos import Point
from products.models import Product

from .models import Farm


class FarmProfileForm(forms.ModelForm):
    lat = forms.FloatField(label='Latitude', min_value=-90, max_value=90)
    lng = forms.FloatField(label='Longitude', min_value=-180, max_value=180)
    products = forms.ModelMultipleChoiceField(  # FR-07: farmer selects what they sell
        queryset=Product.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Products you sell',
        help_text='Only these appear on your daily update screen.',
    )

    class Meta:
        model = Farm
        fields = [
            'name', 'pickup_hours', 'contact_phone',
            'whatsapp_number', 'show_exact_pin',
        ]
        widgets = {
            'pickup_hours': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_contact_phone(self):
        from accounts.forms import normalize_phone
        return normalize_phone(self.cleaned_data['contact_phone'])

    def clean_whatsapp_number(self):
        raw = self.cleaned_data['whatsapp_number']
        return normalize_phone(raw) if raw else ''

    def save(self, commit=True):
        farm = super().save(commit=False)
        farm.location = Point(
            self.cleaned_data['lng'], self.cleaned_data['lat'], srid=4326,
        )
        if commit:
            farm.save()
        return farm
