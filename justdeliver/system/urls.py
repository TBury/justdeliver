from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard),
    path('Deliveries/select-delivery-method/', views.select_delivery_adding_mode),
]
