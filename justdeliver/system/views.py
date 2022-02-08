from django.shortcuts import render, redirect
from .models import Driver, Disposition, DeliveryScreenshot
from django.http import HttpResponse


def dashboard(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    info = driver.get_driver_info()
    return render(request, "dashboard.html", info)


def select_delivery_adding_mode(request):
    return render(request, "choose_delivery_method.html")


def upload_screenshots(request):
    if request.method == "POST":
        delivery_key = DeliveryScreenshot.process_screenshots(
            user=request.user,
            screenshots=request.FILES,
        )

        #uuid serialization error forces casting to string
        request.session["delivery_key"] = str(delivery_key)
        return HttpResponse(status=200, content="Poprawnie utworzono list przewozowy.")
    else:
        return HttpResponse(status=405, content="Błędna metoda HTTP. Upewnij się, "
                                                     "że korzystasz z formularza do screenshotów.")


def add_delivery_details(request):
    return render(request, "add_delivery_details.html")
