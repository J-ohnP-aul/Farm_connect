"""Listing model — database-design.md §5.4.

One row per farm–product–day (my call §4.4): renewal is an upsert on the
unique key, which preserves the pilot's weekly-activity history. Freshness
is enforced by the ActiveListingManager — never by the optional midnight
cleanup job (SRS 5.4, C8).
"""

from django.db import models
from django.db.models import Q
from django.utils import timezone


class ActiveListingManager(models.Manager):
    """Default buyer-facing queryset: only active listings (BR-07).

    SDD §5.2: every buyer-facing view goes through this manager, so expired
    or withdrawn rows are excluded even if the scheduled cleanup never runs.
    """

    def get_queryset(self):
        now = timezone.now()
        return (
            super().get_queryset()
            .filter(expires_at__gt=now, withdrawn_at__isnull=True)
        )


class Listing(models.Model):
    farm = models.ForeignKey('farms.Farm', on_delete=models.CASCADE, related_name='listings')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='listings')
    listing_date = models.DateField()  # pilot-local calendar day
    quantity_note = models.CharField(max_length=140, blank=True)  # FR-14
    price_kes = models.DecimalField(  # optional, non-negative (C7)
        max_digits=8, decimal_places=2, null=True, blank=True,
    )
    withdrawn_at = models.DateTimeField(null=True, blank=True)  # early "sold out"
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # midnight end of listing_date (FR-16)

    class Meta:
        constraints = [
            models.UniqueConstraint(  # renewal upsert key
                fields=['farm', 'product', 'listing_date'], name='unique_farm_product_day',
            ),
            models.CheckConstraint(check=Q(expires_at__gt=models.F('created_at')), name='expiry_after_creation'),
            models.CheckConstraint(check=Q(price_kes__gte=0), name='price_non_negative'),
        ]
        indexes = [
            models.Index(fields=['product', 'expires_at'], name='listing_product_expiry_idx'),
            models.Index(fields=['farm', 'listing_date'], name='listing_farm_date_idx'),
        ]

    objects = models.Manager()
    active = ActiveListingManager()

    def __str__(self):
        return f'{self.farm} — {self.product} — {self.listing_date}'
