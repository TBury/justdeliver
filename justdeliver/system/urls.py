from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard),
    path('Deliveries/select-delivery-method/', views.select_delivery_adding_mode),
    path('api/Delivery/send-screenshots', views.upload_screenshots, name="upload_screenshots"),
    path('Deliveries/add-delivery-details', views.add_delivery_details),
    path('drivers-card/', views.drivers_card),
]
