from django.urls import path
from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('', views.home),
    path('Register', views.register),
    path('login', LoginView.as_view(template_name="login.html"), name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('Deliveries/select-delivery-method/', views.select_delivery_adding_mode),
    path('ActivationSent', views.account_activation_sent, name='account_activation_sent'),
    path(r'activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})',
        views.activate, name='activate'),
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
    path('Deliveries/', views.driver_deliveries, name='driver_deliveries'),
    path('Company/Deliveries', views.delivery_office),
    path('Deliveries/<int:delivery_id>', views.show_delivery_details),
    path('Deliveries/EditDelivery/<int:delivery_id>', views.edit_delivery_details),
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
    path('Company/Dispositions/ManageDisposition/<int:disposition_id>', views.manage_disposition),
    path('Company/Preferences', views.company_preferences),
    path('Company/DeleteCompany', views.delete_company),
    path('Company/Applications', views.show_company_applications),
    path('Company/Applications/<int:application_id>', views.check_application),
    path('Company/Applications/<int:application_id>/AcceptApplication', views.accept_application),
    path('Company/Applications/<int:application_id>/RejectApplication', views.reject_application),
]
