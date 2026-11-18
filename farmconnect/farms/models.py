"""Farm model — database-design.md §5.2.

Privacy is enforced by the schema: `location` (exact) is a private column
never selected by public querysets; `public_location` is the grid-snapped
copy that buyer-facing queries return. `is_active` is the curated-pilot
visibility gate (my call #10, database-design.md §12).
"""

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models

from .services import grid_snap


class Farm(models.Model):
    # PROTECT: deactivate users, never delete pilot history (my call #8).
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='farm',
    )
    name = models.CharField(max_length=140)
    location = gis_models.PointField(srid=4326)  # exact — private
    public_location = gis_models.PointField(srid=4326)  # grid-snapped copy
    show_exact_pin = models.BooleanField(default=False)  # opt-in (FR-08/09)
    is_active = models.BooleanField(default=False)  # admin onboarding gate
    pickup_hours = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=20)  # E.164
    whatsapp_number = models.CharField(max_length=20, blank=True)
    products = models.ManyToManyField('products.Product', blank=True, related_name='farms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Database-design.md §8: spatial index on location (GistIndex on
        # PostGIS; SpatiaLite builds its R-tree automatically).
        indexes = [
            gis_models.Index(fields=['location'], name='farm_location_idx'),
        ]

    def save(self, *args, **kwargs):
        # Grid-snap on every save (SDD §5.3): public_location is stored,
        # never computed per-request (per-request jitter would leak the
        # true centroid through averaging).
        self.public_location = grid_snap(self.location)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
