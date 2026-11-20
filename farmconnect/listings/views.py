"""Farmer daily-update views — UC-03: publish today's availability.

The daily update screen is the product's most important screen (<10 s,
FR-19): toggles pre-filled from YESTERDAY (renew-by-default), optional
price/note revealed per product, one submit.
"""

from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from listings.models import Listing
from listings.services import local_today, publish_for_today
from products.models import Product


def _products_for(farm):
    """FR-07: show only the products the farmer selected on their profile;
    a profile with no selection (transitional) falls back to the catalogue."""
    if farm.products.exists():
        return farm.products.filter(is_active=True)
    return Product.objects.filter(is_active=True)


@login_required
def daily_update(request):
    farm = getattr(request.user, 'farm', None)
    if farm is None:
        messages.warning(request, 'Create your farm profile first.')
        return redirect('farm_edit')

    today = local_today()
    products = _products_for(farm)
    todays_rows = {l.product_id: l for l in Listing.objects.filter(farm=farm, listing_date=today)}
    # Renew-by-default: when nothing is published yet today, start from
    # yesterday's availability so the morning flow is open-tap-save.
    yesterday_rows = {}
    if not todays_rows:
        yesterday_rows = {
            l.product_id: l for l in Listing.objects.filter(
                farm=farm, listing_date=today - timezone.timedelta(days=1),
                withdrawn_at__isnull=True,
            )
        }

    if request.method == 'POST':
        # Parse everything first, so an error can re-render with the
        # farmer's entries intact instead of wiping the form.
        details = {}
        entered = {}
        valid = True
        for product in products:
            checked = request.POST.get(f'available_{product.slug}') == 'on'
            raw_price = request.POST.get(f'price_{product.slug}', '').strip()
            note = request.POST.get(f'note_{product.slug}', '').strip()
            price = None
            if checked and raw_price:
                try:
                    price = Decimal(raw_price)
                    if price < 0:
                        raise InvalidOperation
                except InvalidOperation:
                    messages.error(request, f'Invalid price for {product.name} — fix it and save again.')
                    valid = False
            if checked:
                details[product.slug] = {'price_kes': price, 'quantity_note': note}
            entered[product.id] = {'checked': checked, 'price': raw_price, 'note': note}

        if valid:
            created, renewed = publish_for_today(farm, details)
            messages.success(request, f'Availability saved: {created} new, {renewed} renewed.')
            return redirect('dashboard')

        # re-render with what the farmer typed
        context_products = []
        for p in products:
            e = entered.get(p.id, {})
            context_products.append({
                'product': p,
                'checked': e.get('checked', False),
                'price': e.get('price', ''),
                'note': e.get('note', ''),
            })
        return render(request, 'listings/daily_update.html', {
            'farm': farm,
            'products': context_products,
            'carried': False,
        })

    def context_row(p):
        row = todays_rows.get(p.id) or yesterday_rows.get(p.id)
        return {'product': p, 'listing': row}

    context = {
        'farm': farm,
        'products': [context_row(p) for p in products],
        'carried': bool(yesterday_rows) and not todays_rows,
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
        messages.success(request, 'Marked sold out. Bring it back any time from "Update today\'s availability".')
    return redirect('dashboard')
