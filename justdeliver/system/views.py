from django.shortcuts import render
from .models import Driver, Disposition


def dashboard(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    info = driver.get_driver_info()
    return render(request, "dashboard.html", info)
