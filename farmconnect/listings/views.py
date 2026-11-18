"""Farmer daily-update views — UC-03: publish today's availability.

The daily update screen is the product's most important screen (<10 s,
FR-19): pre-checked toggles, optional price/note, one submit.
"""

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from listings.models import Listing
from listings.services import local_today, publish_for_today
from products.models import Product


@login_required
def daily_update(request):
    farm = getattr(request.user, 'farm', None)
    if farm is None:
        messages.warning(request, 'Create your farm profile first.')
        return redirect('farm_edit')

    today = local_today()
    products = Product.objects.filter(is_active=True)
    existing = {l.product_id: l for l in Listing.objects.filter(farm=farm, listing_date=today)}

    if request.method == 'POST':
        details = {}
        for product in products:
            if request.POST.get(f'available_{product.slug}') != 'on':
                continue
            raw_price = request.POST.get(f'price_{product.slug}', '').strip()
            price = None
            if raw_price:
                try:
                    price = Decimal(raw_price)
                    if price < 0:
                        raise InvalidOperation
                except InvalidOperation:
                    messages.error(request, f'Invalid price for {product.name}.')
                    return redirect('daily_update')
            details[product.slug] = {
                'price_kes': price,
                'quantity_note': request.POST.get(f'note_{product.slug}', '').strip(),
            }
        created, renewed = publish_for_today(farm, details)
        messages.success(request, f'Availability saved: {created} new, {renewed} renewed.')
        return redirect('dashboard')

    context = {
        'farm': farm,
        'products': [
            {
                'product': p,
                'listing': existing.get(p.id),
            }
            for p in products
        ],
    }
    return render(request, 'listings/daily_update.html', context)


@login_required
def withdraw(request, listing_id):
    """Early 'sold out' removal (my call #3, database-design.md §12)."""
    listing = Listing.objects.filter(
        pk=listing_id, farm=request.user.farm, withdrawn_at__isnull=True,
    ).first()
    if listing:
        listing.withdrawn_at = timezone.now()
        listing.save(update_fields=['withdrawn_at'])
        messages.success(request, 'Listing marked sold out.')
    return redirect('dashboard')
