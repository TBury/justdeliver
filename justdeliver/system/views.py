from django.shortcuts import render
from .models import Driver


def dashboard(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    statistics = driver.get_statistics()
    return render("dashboard.html", statistics)
