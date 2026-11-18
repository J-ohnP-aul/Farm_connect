"""Root URL configuration — SDD §4 module map."""

from django.contrib import admin
from django.urls import include, path

from core import views as core_views
from farms import views as farm_views

urlpatterns = [
    path('', core_views.landing, name='landing'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('map/', include('discovery.urls')),
    path('dashboard/', farm_views.dashboard, name='dashboard'),
    path('farm/', include('farms.urls')),
    path('availability/', include('listings.urls')),
]
