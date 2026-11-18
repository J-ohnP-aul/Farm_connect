from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import ContactEvent, Place


@admin.register(Place)
class PlaceAdmin(GISModelAdmin):
    """Curated manual-location registry — seeded per pilot area (§4.2)."""
    list_display = ('name', 'slug', 'search_radius_m', 'is_active', 'display_order')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ContactEvent)
class ContactEventAdmin(admin.ModelAdmin):
    list_display = ('farm', 'channel', 'created_at')
    list_filter = ('channel',)
    date_hierarchy = 'created_at'
    # Read-only by nature: nothing about buyers is stored, and events are
    # written only by the contact redirect endpoint.
    def has_add_permission(self, request):
        return False
