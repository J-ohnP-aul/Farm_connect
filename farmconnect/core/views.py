"""Core views: landing page (SDD §4 — core owns shared pages)."""

from django.shortcuts import redirect, render


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')
