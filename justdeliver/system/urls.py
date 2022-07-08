from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard),
    path('Deliveries/select-delivery-method/', views.select_delivery_adding_mode),
    path('api/Delivery/send-screenshots', views.upload_screenshots, name="upload_screenshots"),
    path('Deliveries/add-delivery-details', views.add_delivery_details),
    path('drivers-card/', views.drivers_card),
    path('dispositions/', views.show_dispositions),
    path('Dispositions/generate-disposition', views.generate_disposition),
    path('Dispositions/AcceptDisposition/<int:disposition_id>', views.accept_disposition),
    path('Dispositions/DeleteDisposition/<int:disposition_id>', views.delete_disposition),
    path('Dispositions/CancelDisposition/<int:disposition_id>', views.cancel_disposition),
    path('vehicles/', views.show_vehicles),
    path('vehicles/add-new-vehicle', views.add_new_vehicle),
    path('Vehicles/EditVehicle/<int:vehicle_id>', views.edit_vehicle),
    path('Vehicles/SelectVehicle/<int:vehicle_id>', views.select_vehicle),
    path('Vehicles/DeleteVehicle/<int:vehicle_id>', views.delete_vehicle),
    path('offers-market', views.show_offers),
    path('OffersMarket/AcceptOffer/<int:offer_id>', views.accept_offer),
    path('create-new-company', views.create_company),
    path('find-company', views.find_company),
    path('Company/<int:company_id>', views.show_company_details),
    path('Company/SendApplication/<int:company_id>', views.employee_application),
    path('Deliveries/', views.delivery_office),
    path('Delivery/<int:delivery_id>', views.show_delivery_details),
    path('Deliveries/ChangeDeliveryStatus', views.edit_delivery_status),
    path('Company/ManageDrivers', views.manage_drivers),
    path('Company/Drivers/<int:employee_id>', views.company_driver_details),
    path('Company/Drivers/<int:employee_id>/EditProfile', views.edit_driver_profile),
    path('Company/Drivers/DismissDriver/<int:employee_id>', views.dismiss_driver),
    path('Company/Drivers/HireDriver', views.hire_driver),
    path('Drivers/FindDriver/<str:nickname>', views.find_driver),
    path('Company/Vehicles', views.show_company_vehicles),
    path('Company/Vehicles/AddNewVehicle', views.add_new_vehicle),
    path('Company/Dispositions', views.show_company_dispositions),
]
