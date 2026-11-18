"""Listing upsert service — SDD §5.2 / database-design.md §4.4.

Publishing today's availability creates or renews one row per
farm–product–day. Expiry is midnight at the end of the pilot-local
calendar day (FR-16), computed in settings.TIME_ZONE.
"""

from datetime import datetime, time

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from zoneinfo import ZoneInfo


def expires_at_for(listing_date):
    """Midnight at the end of `listing_date`, in the pilot's timezone."""
    tz = ZoneInfo(settings.TIME_ZONE)
    end_of_day = datetime.combine(
        listing_date, time(23, 59, 59, 999999), tzinfo=tz,
    )
    return end_of_day.astimezone(ZoneInfo('UTC'))


def local_today():
    return timezone.localdate()


@transaction.atomic
def publish_for_today(farm, product_slugs_with_details):
    """Create/renew today's listings for `farm`.

    `product_slugs_with_details` maps slug -> {'price_kes': Decimal|None,
    'quantity_note': str}. Existing rows for the same (farm, product,
    listing_date) are renewed in place; rows for products left untoggled
    are withdrawn early (sold out) so they leave discovery at once.
    Returns (created_count, renewed_count).
    """
    from .models import Listing  # local import avoids circularity at load
    from products.models import Product

    today = local_today()
    expiry = expires_at_for(today)
    created = renewed = 0

    products = Product.objects.filter(slug__in=product_slugs_with_details, is_active=True)
    for product in products:
        details = product_slugs_with_details[product.slug]
        listing, was_created = Listing.objects.update_or_create(
            farm=farm, product=product, listing_date=today,
            defaults={
                'price_kes': details.get('price_kes'),
                'quantity_note': details.get('quantity_note', ''),
                'expires_at': expiry,
                'withdrawn_at': None,
            },
        )
        if was_created:
            created += 1
        else:
            renewed += 1

    # Early removal (my call #3, database-design.md §12): anything the
    # farmer did not include in this update is marked sold out.
    Listing.objects.filter(
        farm=farm, listing_date=today, withdrawn_at__isnull=True,
    ).exclude(
        product__slug__in=product_slugs_with_details,
    ).update(withdrawn_at=timezone.now())

    return created, renewed
