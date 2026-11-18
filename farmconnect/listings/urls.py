from django.urls import path

from . import views

urlpatterns = [
    path('update/', views.daily_update, name='daily_update'),
    path('withdraw/<int:listing_id>/', views.withdraw, name='withdraw'),
]
