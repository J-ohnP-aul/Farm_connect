"""DiscoveryService — SDD §5.1.

The only module with spatial SQL. Buyer-facing queries run here and
nowhere else, so the SpatiaLite → PostGIS migration is confined to this
file (database-design.md §10):

- PostGIS: distance filter via geography cast (metres, exact).
- SpatiaLite: no geography type — transform both the farm point and the
  search origin to the pilot's UTM zone (settings.PILOT_UTM_SRID) and
  compare metres there.

Privacy rules enforced here (NFR-05/06):
- distance filters run on the EXACT farm location (correct membership),
- the returned pin honours show_exact_pin,
- contact fields are never included in bulk results,
- farms with is_active=False or deactivated owners are excluded.
"""

from django.conf import settings
from django.contrib.gis.db.models.functions import Transform
from django.contrib.gis.measure import D

from farms.models import Farm
from listings.models import Listing
from products.models import Product


def _distance_filter(qs, origin, radius_m):
    """Apply a metre-based radius filter that works on both backends.

    On SpatiaLite we compare in a planar UTM system: transform the farm
    point and the origin to settings.PILOT_UTM_SRID, then use D(m=...).
    Django's Distance lookups operate in degrees when both geometries are
    4326 on SpatiaLite, which is meaningless for a 15 km radius.
    """
    utm = settings.PILOT_UTM_SRID
    qs = qs.annotate(location_utm=Transform('location', utm))
    origin_utm = origin.transform(utm, clone=True)
    return qs.filter(location_utm__distance_lte=(origin_utm, D(m=radius_m)))


def _active_listings():
    return (
        Listing.active.select_related('product')
        .filter(farm__is_active=True, farm__owner__is_active=True)
    )


def nearby_farms(origin, product_slug=None, radius_m=None):
    """Return farms near `origin` with their active listings.

    `origin` is a GEOS Point (SRID 4326) — either the buyer's GPS location
    or a Place's coordinates. Returns a list of dicts shaped for the map
    JSON endpoint; contact fields are deliberately absent.
    """
    radius_m = radius_m or settings.DEFAULT_SEARCH_RADIUS_M

    farms = _distance_filter(
        Farm.objects.filter(is_active=True, owner__is_active=True),
        origin, radius_m,
    )

    listings = _active_listings()
    if product_slug:
        listings = listings.filter(product__slug=product_slug)

    by_farm = {}
    for listing in listings.select_related('farm', 'product'):
        by_farm.setdefault(listing.farm_id, []).append({
            'product': listing.product.name,
            'product_slug': listing.product.slug,
            'price_kes': str(listing.price_kes) if listing.price_kes else None,
            'quantity_note': listing.quantity_note or '',
            'expires_at': listing.expires_at.isoformat(),
        })

    results = []
    for farm in farms:
        farm_listings = by_farm.get(farm.id, [])
        if product_slug and not farm_listings:
            continue  # inside the radius but nothing active today
        results.append({
            'id': farm.id,
            'name': farm.name,
            'pickup_hours': farm.pickup_hours,
            # Pin choice honours the farmer's opt-in (BR-08); the exact
            # location leaves the database only for opted-in farms.
            'pin': {
                'lat': farm.location.y if farm.show_exact_pin else farm.public_location.y,
                'lng': farm.location.x if farm.show_exact_pin else farm.public_location.x,
                'approximate': not farm.show_exact_pin,
            },
            'listings': farm_listings,
        })
    return results


def product_options():
    """Active catalogue entries for the filter UI (FR-24)."""
    return list(Product.objects.filter(is_active=True).order_by('name'))


def places():
    """Active curated origins for the manual location picker (FR-22)."""
    from .models import Place
    return list(Place.objects.filter(is_active=True))


def farm_detail(farm_id):
    """Farm detail payload — the ONLY place contact fields are exposed.

    Served on the farm detail view (FR-26/FR-30); never in bulk/map data.
    """
    try:
        farm = Farm.objects.get(pk=farm_id, is_active=True, owner__is_active=True)
    except Farm.DoesNotExist:
        return None
    listings = _active_listings().filter(farm=farm)
    return {
        'id': farm.id,
        'name': farm.name,
        'pin': {
            'lat': farm.location.y if farm.show_exact_pin else farm.public_location.y,
            'lng': farm.location.x if farm.show_exact_pin else farm.public_location.x,
            'approximate': not farm.show_exact_pin,
        },
        'pickup_hours': farm.pickup_hours,
        'contact_phone': farm.contact_phone,
        'whatsapp_number': farm.whatsapp_number or farm.contact_phone,
        'listings': [
            {
                'id': l.id,
                'product': l.product.name,
                'price_kes': str(l.price_kes) if l.price_kes else None,
                'quantity_note': l.quantity_note or '',
            }
            for l in listings
        ],
    }
