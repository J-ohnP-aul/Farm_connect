from django.contrib import admin

from .models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('farm', 'product', 'listing_date', 'price_kes', 'withdrawn_at', 'expires_at')
    list_filter = ('listing_date', 'product')
    search_fields = ('farm__name',)
    date_hierarchy = 'listing_date'
