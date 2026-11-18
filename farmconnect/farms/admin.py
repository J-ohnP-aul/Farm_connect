from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Farm


@admin.register(Farm)
class FarmAdmin(GISModelAdmin):
    """Admin shows the map so onboarding staff can verify pins (FR-35/36).

    Farm activation happens here: is_active False until an admin flips it
    during in-person onboarding (curated pilot, SDD §8).
    """
    list_display = ('name', 'owner', 'is_active', 'show_exact_pin', 'updated_at')
    list_filter = ('is_active', 'show_exact_pin')
    search_fields = ('name', 'owner__phone_number', 'owner__name')
    list_editable = ('is_active',)
