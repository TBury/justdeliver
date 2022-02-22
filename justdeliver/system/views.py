from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Driver, Disposition, DeliveryScreenshot, Delivery, Vehicle, Offer, Company, Employee
from .forms import NewDeliveryForm, NewVehicleForm, EditVehicleForm, CreateCompanyForm


def dashboard(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    info = driver.get_driver_info()
    context = {
        "dashboard": "option--active",
        "info": info,
    }
    return render(request, "dashboard.html", context)


def select_delivery_adding_mode(request):
    context = {
        "add_new_delivery": "option--active",
    }
    return render(request, "choose_delivery_method.html", context)


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
        driver = Driver.get_driver_by_user_profile(request.user)
        try:
            delivery = Delivery.objects.get(delivery_key=delivery_key)
            if request.method == "POST":
                form = NewDeliveryForm(request.POST, instance=delivery)
                if form.is_valid():
                    delivery.is_edited = False
                    delivery.driver = driver
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
                    'add_new_delivery': 'option--active'
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
        "info": info,
        "drivers_card": "option--active",
    }
    return render(request, "drivers_card.html", context)


def show_dispositions(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    current_disposition = Disposition.get_disposition_for_driver(driver)
    dispositions = Disposition.get_unaccepted_dispositions(driver)
    context = {
        'current_disposition': current_disposition,
        'dispositions': dispositions,
        'dispositions_tag': "option--active",
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
        'vehicles_tag': "option--active",
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
            'vehicles_tag': "option--active",
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
                'vehicles_tag': "option--active",
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
    offers_list = Offer.get_offers()
    paginator = Paginator(offers_list, 10)
    page = request.GET.get('page')
    try:
        offers = paginator.page(page)
    except PageNotAnInteger:
        offers = paginator.page(1)
    except EmptyPage:
        offers = paginator.page(paginator.num_pages)

    context = {
        "offers": offers,
        "offers_market": "option--active",
    }
    return render(request, "offers_market.html", context)


def accept_offer(request, offer_id):
    offer = Offer.get_offer_by_id(offer_id)
    if offer:
        driver = Driver.get_driver_by_user_profile(request.user)
        result = offer.accept_offer(driver)
        if result.get("message"):
            return redirect("/dispositions")
        else:
            return HttpResponse(status=403, content=result.get("error"))
    else:
        return HttpResponse(status=403, content="Oferta nie istnieje.")


def create_company(request):
    if request.method == "POST":
        form = CreateCompanyForm(request.POST)
        if form.is_valid():
            company = form.save()
            driver = Driver.get_driver_by_user_profile(request.user)
            Employee.create_employee(driver, company, "Właściciel")
            return redirect("/dashboard")
        else:
            return HttpResponse(content=form.errors)
    else:
        context = {
            'form': CreateCompanyForm(),
            "create_company": "option--active",
        }
        return render(request, "create_company.html", context)


def find_company(request):
    companies_list = Company.get_all_companies()
    paginator = Paginator(companies_list, 10)
    page = request.GET.get('page')
    try:
        companies = paginator.page(page)
    except PageNotAnInteger:
        companies = paginator.page(1)
    except EmptyPage:
        companies = paginator.page(paginator.num_pages)

    context = {
        "companies": companies,
        "find_company": "option--active",
    }

    return render(request, "find_company.html", context)


def show_company_details(request, company_id):
    company = Company.get_company_by_id(company_id)
    info = company.get_company_info()
    context = {
        "info": info,
        "find_company": "option--active",
    }
    return render(request, "company_details.html", context)
