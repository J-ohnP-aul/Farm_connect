"""Farmer registration and sign-in — SRS FR-01/FR-02 (UC-02).

Registration creates a farmer; a farm profile is a separate step (farms
app). Django's built-in auth views handle sign-in.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import FarmerRegistrationForm


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = FarmerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Welcome! Now create your farm profile.')
        return redirect('farm_edit')
    return render(request, 'accounts/register.html', {'form': form})
