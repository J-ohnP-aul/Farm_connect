from django.urls import path

from . import views

urlpatterns = [
    path('edit/', views.farm_edit, name='farm_edit'),
]
