import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Driver, Disposition, DeliveryScreenshot, Delivery, Vehicle, Offer, Company, Employee
from .forms import NewDeliveryForm, NewVehicleForm, EditVehicleForm, CreateCompanyForm, NewApplicationForm, \
    EditEmployeeForm


def dashboard(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    info = driver.get_driver_info()
    context = {
        "dashboard": "option--active",
        "info": info,
        "is_employed": driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
    }
    return render(request, "dashboard.html", context)


def select_delivery_adding_mode(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    context = {
        "add_new_delivery": "option--active",
        "is_employed": driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
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
                    'add_new_delivery': 'option--active',
                    "is_employed": driver.is_employed,
                    "has_speditor_permissions": driver.has_speditor_permissions,
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
        "is_employed": driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
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
        'is_employed': driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
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
    if not driver.is_employed or (driver.is_employed and driver.job_title == "owner" or driver.job_title == "speditor"):
        try:
            Disposition.delete_disposition(driver, disposition_id)
            return redirect("/dispositions")
        except Disposition.DoesNotExist:
            return HttpResponse(status=403, content="Dyspozycja nie istnieje.")
    else:
        return HttpResponse(status=403, content="Nie masz uprawnień do usuwania dyspozycji.")


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
        'is_employed': driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
    }
    return render(request, "vehicles.html", context)


def add_new_vehicle(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    if not driver.is_employed or (driver.is_employed and driver.job_title == "owner" or driver.job_title == "speditor"):
        if request.method == "POST":
            form = NewVehicleForm(request.POST)
            if form.is_valid():
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
                'is_employed': driver.is_employed,
                "has_speditor_permissions": driver.has_speditor_permissions,
            }
            return render(request, "add_new_vehicle.html", context)
    else:
        return HttpResponse(status=403, content="Nie masz uprawnień do dodawania nowego pojazdu.")


def edit_vehicle(request, vehicle_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    if not driver.is_employed or (driver.is_employed and driver.job_title == "owner" or driver.job_title == "speditor"):
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
                    'is_employed': driver.is_employed,
                    "has_speditor_permissions": driver.has_speditor_permissions,
                }
                return render(request, "edit_vehicle.html", context)
        else:
            return HttpResponse(status=403, content="Pojazd nie istnieje.")
    else:
        return HttpResponse(status=403, content="Nie masz uprawnień do edycji pojazdu.")


def select_vehicle(request, vehicle_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    if not driver.is_employed or (driver.is_employed and driver.job_title == "owner" or driver.job_title == "speditor"):
        messages = Vehicle.change_selected_vehicle(driver, vehicle_id)
        if messages.get("error"):
            return HttpResponse(status=403, content="Pojazd nie istnieje.")
        return redirect("/vehicles")
    else:
        return HttpResponse(status=403, content="Nie masz uprawnień do wybierania innego pojazdu.")


def show_offers(request):
    driver = Driver.get_driver_by_user_profile(request.user)
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
        'is_employed': driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
    }
    return render(request, "offers_market.html", context)


def accept_offer(request, offer_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    if not driver.is_employed or (driver.is_employed and driver.job_title == "owner" or driver.job_title == "speditor"):
        offer = Offer.get_offer_by_id(offer_id)
        if offer:
            result = offer.accept_offer(driver)
            if result.get("message"):
                return redirect("/dispositions")
            else:
                return HttpResponse(status=403, content=result.get("error"))
        else:
            return HttpResponse(status=403, content="Oferta nie istnieje.")
    else:
        return HttpResponse(status=403, content="Nie masz uprawnień do akceptowania oferty.")


def create_company(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    if not driver.is_employed:
        if request.method == "POST":
            form = CreateCompanyForm(request.POST)
            if form.is_valid():
                company = form.save()
                Employee.create_employee(driver, company, "Właściciel")
                return redirect("/dashboard")
            else:
                return HttpResponse(content=form.errors)
        else:
            context = {
                'form': CreateCompanyForm(),
                "create_company": "option--active",
                'is_employed': driver.is_employed,
                "has_speditor_permissions": driver.has_speditor_permissions,
            }
        return render(request, "create_company.html", context)
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do utworzenia firmy.")


def find_company(request):
    driver = Driver.get_driver_by_user_profile(request.user)
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
        'is_employed': driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
    }

    return render(request, "find_company.html", context)


def show_company_details(request, company_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    company = Company.get_company_by_id(company_id)
    info = company.get_company_info()
    context = {
        "info": info,
        "find_company": "option--active",
        'is_employed': driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
    }
    return render(request, "company_details.html", context)


def employee_application(request, company_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    if not driver.is_employed:
        if request.method == "POST":
            form = NewApplicationForm(request.POST)
            if form.is_valid():
                application = form.save(commit=False)
                application.driver = driver
                company = Company.get_company_by_id(company_id)
                application.company = company
                application.save()
                return redirect("/dashboard")
            else:
                return HttpResponse(content=form.errors)
        else:
            context = {
                'form': NewApplicationForm(),
                "find_company": "option--active",
                'is_employed': driver.is_employed,
                "has_speditor_permissions": driver.has_speditor_permissions,
            }
            return render(request, "new_application_form.html", context)
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wysyłania podania o pracę.")


def delivery_office(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    if driver.is_employed:
        if driver.company and (driver.job_title == "owner" or driver.job_title == "speditor"):
            company = driver.company
            deliveries_list = Delivery.get_all_company_deliveries(driver, company)
            if deliveries_list:
                paginator = Paginator(deliveries_list, 10)
                page = request.GET.get('page')

                try:
                    deliveries = paginator.page(page)
                except PageNotAnInteger:
                    deliveries = paginator.page(1)
                except EmptyPage:
                    deliveries = paginator.page(paginator.num_pages)

                context = {
                    "deliveries": deliveries,
                    "delivery_office": "option--active",
                    'is_employed': driver.is_employed,
                    "has_speditor_permissions": driver.has_speditor_permissions,
                }

                return render(request, "delivery_office.html", context)
            else:
                return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def show_delivery_details(request, delivery_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    if driver.is_employed:
        if driver.company and (driver.job_title == "owner" or driver.job_title == "speditor"):
            try:
                delivery = Delivery.get_delivery_by_id(delivery_id)
                if delivery.driver.company == driver.company:
                    screenshots = delivery.get_delivery_screenshots()
                    disposition = Disposition.get_disposition_from_waybill(
                        driver=driver,
                        loading_city=delivery.loading_city,
                        unloading_city=delivery.unloading_city,
                        cargo=delivery.cargo,
                    )
                    context = {
                        'delivery': delivery,
                        'screenshots': screenshots,
                        'disposition': disposition,
                        'delivery_office': 'option--active',
                        'is_employed': driver.is_employed,
                        "has_speditor_permissions": driver.has_speditor_permissions,
                    }
                    return render(request, "delivery_details.html", context)
                else:
                    return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
            except Delivery.DoesNotExist:
                return HttpResponse(status=404, content="Dostawa o podanym id nie została znaleziona.")
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def edit_delivery_status(request):
    if request.method == "POST":
        body = json.loads(request.body.decode("utf-8"))
        driver = Driver.get_driver_by_user_profile(request.user)
        if driver.is_employed:
            if driver.company and (driver.job_title == "owner" or driver.job_title == "speditor"):
                try:
                    delivery_id = body.get("delivery_id")
                    delivery = Delivery.get_delivery_by_id(delivery_id)
                    if delivery.driver.company == driver.company:
                        status = body.get("status")
                        message = delivery.update_status(status)
                        if not message.get("error"):
                            return HttpResponse(status=200, content=message.get("message"))
                        else:
                            return HttpResponse(status=400, content="Błędny status dostawy.")
                    else:
                        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
                except ValueError:
                    return HttpResponse(status=400, content="Błędne id dostawy.")
            else:
                return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=405, content="Metoda niedozwolona. Wykonaj operację, korzystając z przycisku w"
                                                " szczegółach zlecenia.")


def manage_drivers(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    if driver.is_employed:
        if driver.company and driver.job_title == "owner":
            company = driver.company
            company_drivers_list = Employee.get_all_company_employees(company)
            if company_drivers_list:
                paginator = Paginator(company_drivers_list, 10)
                page = request.GET.get('page')

                try:
                    company_drivers = paginator.page(page)
                except PageNotAnInteger:
                    company_drivers = paginator.page(1)
                except EmptyPage:
                    company_drivers = paginator.page(paginator.num_pages)

                context = {
                    "company_drivers": company_drivers,
                    "manage_drivers": "option--active",
                    'is_employed': driver.is_employed,
                    "has_speditor_permissions": driver.has_speditor_permissions,
                }

                return render(request, "manage_drivers.html", context)
            else:
                return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def company_driver_details(request, employee_id):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    employee = Employee.get_employee_by_id(employee_id)
    if current_driver.is_employed and employee:
        if current_driver.company == employee.company:
            info = employee.get_driver_info()
            context = {
                "info": info,
                "manage_drivers": "option--active",
                "is_employed": current_driver.is_employed,
                "has_speditor_permissions": current_driver.has_speditor_permissions,
            }
            return render(request, "drivers_card.html", context)
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def edit_driver_profile(request, employee_id):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    employee = Employee.get_employee_by_id(employee_id)
    if current_driver.is_employed and employee:
        if current_driver.company and current_driver.job_title == "owner" and current_driver.company == employee.company:
            if request.method == "POST" and request.POST:
                form = EditEmployeeForm(request.POST, instance=employee)
                if form.is_valid():
                    form.save()
                    return redirect("/Company/ManageDrivers")
                else:
                    return HttpResponse(content=form.errors)
            else:
                info = employee.get_driver_info()
                form = EditEmployeeForm(instance=employee)
                context = {
                    "info": info,
                    "manage_drivers": "option--active",
                    "is_employed": current_driver.is_employed,
                    "has_speditor_permissions": current_driver.has_speditor_permissions,
                    "form": form,
                }
            return render(request, "edit_driver.html", context)
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
