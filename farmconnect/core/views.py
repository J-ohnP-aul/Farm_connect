"""Core views: landing page (SDD §4 — core owns shared pages)."""

from django.conf import settings
from django.contrib.gis.geos import Point
from django.shortcuts import redirect, render

from discovery import services
from products.models import Product


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    # Live pilot truth on the Persuade surface: counts from the same
    # discovery query the map uses, centred on the pilot area.
    centre = Point(
        settings.DEFAULT_MAP_CENTER[1], settings.DEFAULT_MAP_CENTER[0], srid=4326,
    )
    farms = services.nearby_farms(centre)
    place = services.places()
    place_name = place[0].name if place else 'the pilot area'
    context = {
        'products': services.product_options(),
        'open_farms': len(farms),
        'listings_today': sum(len(f['listings']) for f in farms),
        'place_name': place_name,
    }
    return render(request, 'core/landing.html', context)
