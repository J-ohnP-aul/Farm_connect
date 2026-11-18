"""Buyer-side models — database-design.md §5.5 and §5.6.

`Place` is the curated manual-location registry (my call §4.2: no external
geocoder). `ContactEvent` counts buyer contact taps (my call §5.6, required
by the proposal's success metrics) and deliberately stores nothing about
the buyer — no phone, IP, or user agent.
"""

from django.contrib.gis.db import models as gis_models
from django.db import models


class Place(models.Model):
    name = models.CharField(max_length=120)  # town or estate
    slug = models.SlugField(max_length=120, unique=True)
    location = gis_models.PointField(srid=4326)  # search origin
    search_radius_m = models.IntegerField(default=15_000)  # per-place override
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class ContactEvent(models.Model):
    class Channel(models.TextChoices):
        CALL = 'call', 'Call'
        WHATSAPP = 'whatsapp', 'WhatsApp'

    farm = models.ForeignKey('farms.Farm', on_delete=models.PROTECT, related_name='contact_events')
    channel = models.CharField(max_length=10, choices=Channel.choices)
    listing = models.ForeignKey(
        'listings.Listing', null=True, blank=True, on_delete=models.SET_NULL, related_name='contact_events',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['created_at'], name='contact_created_idx')]

    def __str__(self):
        return f'{self.farm} — {self.channel} — {self.created_at:%Y-%m-%d}'
