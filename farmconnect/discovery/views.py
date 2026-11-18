"""Buyer-facing views — SDD §4 (discovery owns the whole buyer side).

- Home/map page: server-rendered shell + Leaflet map fed by the JSON
  endpoint (the project's one JSON interface, SDD §3).
- Farm detail: the only place contact numbers are exposed (FR-30).
- Contact redirect: logs a ContactEvent then 302s to tel:/wa.me (§5.6).
"""

from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from farms.models import Farm
from listings.models import Listing
from products.models import Product

from .models import ContactEvent
from . import services


def home(request):
    """Discovery page: map, product filters, location picker (UC-01)."""
    import json

    from django.conf import settings

    selected_place = request.GET.get('place', '')
    places_json = json.dumps([
        {
            'slug': p.slug, 'name': p.name,
            'lat': p.location.y, 'lng': p.location.x,
            'radius': p.search_radius_m,
        }
        for p in services.places()
    ])
    return render(request, 'discovery/home.html', {
        'products': services.product_options(),
        'places': services.places(),
        'places_json': places_json,
        'selected_place': selected_place,
        'selected_product': request.GET.get('product', ''),
        'map_center': json.dumps(settings.DEFAULT_MAP_CENTER),
        'map_zoom': settings.DEFAULT_MAP_ZOOM,
    })


@require_GET
def map_data(request):
    """JSON map data endpoint (SDD §3) — no phone fields in the response."""
    origin = None
    radius = None

    if request.GET.get('lat') and request.GET.get('lng'):
        try:
            from django.contrib.gis.geos import Point
            origin = Point(float(request.GET['lng']), float(request.GET['lat']), srid=4326)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'invalid coordinates'}, status=400)
    elif request.GET.get('place'):
        for place in services.places():
            if place.slug == request.GET['place']:
                origin = place.location
                radius = place.search_radius_m
                break

    if origin is None:
        return JsonResponse({'error': 'no origin: pass lat/lng or place'}, status=400)

    product_slug = request.GET.get('product') or None
    if product_slug and not Product.objects.filter(slug=product_slug, is_active=True).exists():
        return JsonResponse({'error': 'unknown product'}, status=400)

    farms = services.nearby_farms(origin, product_slug=product_slug, radius_m=radius)
    return JsonResponse({'farms': farms})


def farm_detail(request, farm_id):
    """Farm detail view (UC-04 precondition): availability + contact actions."""
    detail = services.farm_detail(farm_id)
    if detail is None:
        return render(request, 'discovery/farm_not_found.html', status=404)
    return render(request, 'discovery/farm_detail.html', {'farm': detail})


@require_GET
def contact_redirect(request, farm_id, channel):
    """GET /contact/{farm}/{channel} -> log event -> 302 to tel:/wa.me.

    The tap must pass through the server for the pilot's contact metrics
    (database-design.md §5.6). Stores nothing about the buyer.
    """
    if channel not in (ContactEvent.Channel.CALL, ContactEvent.Channel.WHATSAPP):
        return HttpResponseNotFound('unknown channel')
    farm = get_object_or_404(Farm, pk=farm_id, is_active=True, owner__is_active=True)
    listing_id = request.GET.get('listing')
    listing = None
    if listing_id:
        listing = Listing.active.filter(pk=listing_id, farm=farm).first()
    ContactEvent.objects.create(farm=farm, channel=channel, listing=listing)

    if channel == ContactEvent.Channel.CALL:
        target = f'tel:{farm.contact_phone}'
    else:
        number = (farm.whatsapp_number or farm.contact_phone).lstrip('+')
        text = 'Hello! I saw your listing on Local Farm Map.'
        from urllib.parse import quote
        target = f'https://wa.me/{number}?text={quote(text)}'
    # HttpResponse with a manually set Location: Django's response classes
    # reject non-http(s) schemes ('tel:'), but this is the deliberate OS
    # handoff that FR-28/FR-29 require.
    response = HttpResponse(status=302)
    response['Location'] = target
    return response
