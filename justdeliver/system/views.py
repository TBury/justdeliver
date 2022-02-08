from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Driver, Disposition, DeliveryScreenshot, Delivery, Vehicle
from .forms import NewDeliveryForm


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
    if request.session.get("delivery_key"):
        delivery_key = request.session.get("delivery_key")
        try:
            delivery = Delivery.objects.get(delivery_key=delivery_key)
            if request.method == "POST":
                form = NewDeliveryForm(request.POST, instance=delivery)
                if form.is_valid():
                    delivery.is_edited = False
                    form.save()
                    del request.session["delivery_key"]
                return redirect("/dashboard")
            else:
                disposition = Disposition.get_disposition_from_waybill(
                    driver=driver,
                    loading_city=delivery.loading_city,
                    unloading_city=delivery.unloading_city,
                    cargo=delivery.cargo,
                )
                context = {
                    'form': NewDeliveryForm(instance=delivery),
                    'disposition': disposition,
                }
                return render(request, "add_delivery_details.html", context)
        except Delivery.DoesNotExist:
            return HttpResponse(status=403, content="Brak klucza dostawy.")
    else:
        return HttpResponse(status=403, content="Brak klucza dostawy.")


def drivers_card(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    info = driver.get_driver_info()
    context = {
        "info": info
    }
    return render(request, "drivers_card.html", context)


def show_dispositions(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    current_disposition = Disposition.get_disposition_for_driver(driver)
    dispositions = Disposition.get_unaccepted_dispositions(driver)
    context = {
        'current_disposition': current_disposition,
        'dispositions': dispositions,
    }
    return render(request, "dispositions.html", context)


def show_vehicles(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    current_vehicle = Vehicle.get_vehicle_for_driver(driver)
    vehicles = Vehicle.get_driver_vehicles(driver)
    context = {
        'current_vehicle': current_vehicle,
        'vehicles': vehicles,
    }
    return render(request, "vehicles.html", context)
