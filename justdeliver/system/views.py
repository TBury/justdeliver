from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Driver, Disposition, DeliveryScreenshot, Delivery, Vehicle, Offer
from .forms import NewDeliveryForm, NewVehicleForm, EditVehicleForm


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


def generate_disposition(request):
    if request.POST:
        driver = Driver.get_driver_by_user_profile(request.user)
        if Disposition.generate_disposition(driver, request.POST):
            return redirect("/dashboard")
        else:
            return HttpResponse(status=403, content="Błąd generowania dyspozycji.")
    return render(request, "generate_disposition.html")


def accept_disposition(request, disposition_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    try:
        Disposition.accept_disposition(driver, disposition_id)
        return redirect("/dispositions")
    except Disposition.DoesNotExist:
        return HttpResponse(status=403, content="Dyspozycja nie istnieje.")


def delete_disposition(request, disposition_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    try:
        Disposition.delete_disposition(driver, disposition_id)
        return redirect("/dispositions")
    except Disposition.DoesNotExist:
        return HttpResponse(status=403, content="Dyspozycja nie istnieje.")


def cancel_disposition(request, disposition_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    try:
        Disposition.cancel_disposition(driver, disposition_id)
        return redirect("/dispositions")
    except Disposition.DoesNotExist:
        return HttpResponse(status=403, content="Dyspozycja nie istnieje.")


def show_vehicles(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    current_vehicle = Vehicle.get_vehicle_for_driver(driver)
    vehicles = Vehicle.get_driver_vehicles(driver)
    context = {
        'current_vehicle': current_vehicle,
        'vehicles': vehicles,
    }
    return render(request, "vehicles.html", context)


def add_new_vehicle(request):
    if request.method == "POST":
        form = NewVehicleForm(request.POST)
        if form.is_valid():
            driver = Driver.get_driver_by_user_profile(request.user)
            vehicle = form.save(commit=False)
            vehicle.driver_owner = driver
            vehicle.photo = request.FILES.get("photo")
            vehicle.save()
            return redirect("/vehicles")
        else:
            print(form.errors)
    else:
        context = {
            'form': NewVehicleForm(),
        }
        return render(request, "add_new_vehicle.html", context)


def edit_vehicle(request, vehicle_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    vehicle = Vehicle.get_vehicle_from_id(driver, vehicle_id)
    if vehicle:
        if request.method == "POST":
            form = EditVehicleForm(request.POST, instance=vehicle)
            if form.is_valid():
                edited_vehicle = form.save(commit=False)
                edited_vehicle.driver_owner = driver
                if request.FILES.get("photo"):
                    edited_vehicle.photo = request.FILES.get("photo")
                edited_vehicle.save()
                return redirect("/vehicles")
            else:
                print(form.errors)
        else:
            context = {
                'form': EditVehicleForm(instance=vehicle),
                'vehicle': vehicle,
            }
            return render(request, "edit_vehicle.html", context)
    else:
        return HttpResponse(status=403, content="Pojazd nie istnieje.")


def select_vehicle(request, vehicle_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    messages = Vehicle.change_selected_vehicle(driver, vehicle_id)
    if messages.get("error"):
        return HttpResponse(status=403, content="Pojazd nie istnieje.")
    return redirect("/vehicles")


def show_offers(request):
    offers = Offer.get_offers()
    context = {
        "offers": offers
    }
    return render(request, "offers_market.html", context)
