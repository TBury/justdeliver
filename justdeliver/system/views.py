from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Driver, Disposition, DeliveryScreenshot, Delivery
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
