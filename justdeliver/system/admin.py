from django.contrib import admin

from .models import (
    Driver,
    Delivery,
    Disposition,
    Employee,
    Vehicle,
    Company,
    Offer,
    DeliveryScreenshot,
    EmployeeApplication
)

admin.site.register(Driver)
admin.site.register(Employee)
admin.site.register(Delivery)
admin.site.register(Disposition)
admin.site.register(Vehicle)
admin.site.register(Company)
admin.site.register(Offer)
admin.site.register(DeliveryScreenshot)
admin.site.register(EmployeeApplication)