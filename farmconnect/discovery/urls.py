from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('data/', views.map_data, name='map_data'),
    path('farm/<int:farm_id>/', views.farm_detail, name='farm_detail'),
    path('contact/<int:farm_id>/<str:channel>/', views.contact_redirect, name='contact_redirect'),
]
