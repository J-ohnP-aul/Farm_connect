"""Farmer farm-profile views — UC-02 (create) and profile maintenance.

Farm.is_active stays False after self-registration: an admin activates the
farm at in-person onboarding before buyers can see it (SDD §8, my call #10
in database-design.md §12).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from listings.services import local_today
from listings.models import Listing

from .forms import FarmProfileForm


@login_required
def farm_edit(request):
    farm = getattr(request.user, 'farm', None)
    form = FarmProfileForm(request.POST or None, instance=farm)
    if request.method == 'POST' and form.is_valid():
        farm = form.save(commit=False)
        farm.owner = request.user
        farm.save()
        form.save_m2m()
        messages.success(request, 'Farm profile saved.')
        return redirect('dashboard')
    return render(request, 'farms/farm_edit.html', {'form': form, 'farm': farm})


@login_required
def dashboard(request):
    """Farmer dashboard: today's listing state + link to the update screen."""
    farm = getattr(request.user, 'farm', None)
    todays = []
    if farm:
        todays = Listing.objects.filter(farm=farm, listing_date=local_today()).select_related('product')
    return render(request, 'farms/dashboard.html', {'farm': farm, 'todays': todays})
