import json
from django.shortcuts import render, redirect
from django.core import serializers
from django.contrib import messages
from django.contrib.messages import get_messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Driver, Disposition, DeliveryScreenshot, Delivery, Vehicle, Offer, Company, Employee
from .forms import *
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

def home(request):
    return render(request, "home.html")

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Aktywuj swoje konto na JustDeliver!'
            message = render_to_string('account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('account_activation_sent')
        else:
            return HttpResponse(form.errors.as_json())
    else:
        context = {
            "form": SignUpForm()
        }
        return render(request, "register.html", context)

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        driver = Driver.objects.create(user=user)
        driver.nick = user.username
        driver.email_confirmed = True
        user.save()
        driver.save()
        login(request, user)
        return redirect('dashboard')
    else:
        return render(request, 'account_activation_invalid.html')

def account_activation_sent(request):
    return render(request, "account_activation_sent.html")

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
                    messages.success(request, "Dostawa została wysłana poprawnie i oczekuje na zatwierdzenie przez spedycję.")
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
    driver = Driver.get_driver_by_user_profile(request.user)
    if driver.is_employed and driver.job_title == "owner" or driver.job_title == "speditor":
        if request.POST:
            if Disposition.generate_disposition(request.POST.get("driver"), request.POST):
                messages.success(request, "Dyspozycja została wygenerowana poprawnie.")
                return redirect("/Company/Dispositions")
            else:
                return HttpResponse(status=403, content="Błąd generowania dyspozycji.")
        else:
            employees = Employee.get_all_company_employees(driver.company)
            context = {
                'employees': employees,
                'company_dispositions_tag': "option--active",
                'is_employed': driver.is_employed,
                "has_speditor_permissions": driver.has_speditor_permissions,
            }
            return render(request, "generate_disposition.html", context)
    else:
        return HttpResponse(status=403, content="Nie masz uprawnień do generowania dyspozycji.")



def accept_disposition(request, disposition_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    try:
        Disposition.accept_disposition(driver, disposition_id)
        messages.success(request, "Dyspozycja została przyjęta do realizacji. Wykonaj zlecenie o danych z dyspozycji, aby ją zrealizować.")
        return redirect("/dispositions")
    except Disposition.DoesNotExist:
        return HttpResponse(status=403, content="Dyspozycja nie istnieje.")


def delete_disposition(request, disposition_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    if not driver.is_employed or (driver.is_employed and driver.job_title == "owner" or driver.job_title == "speditor"):
        try:
            Disposition.delete_disposition(driver, disposition_id)
            messages.success(request, "Dyspozycja została usunięta poprawnie.")
            return redirect("/dispositions")
        except Disposition.DoesNotExist:
            return HttpResponse(status=403, content="Dyspozycja nie istnieje.")
    else:
        return HttpResponse(status=403, content="Nie masz uprawnień do usuwania dyspozycji.")


def cancel_disposition(request, disposition_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    try:
        Disposition.cancel_disposition(driver, disposition_id)
        messages.success(request, "Dyspozycja została anulowana poprawnie.")
        return redirect("/dispositions")
    except Disposition.DoesNotExist:
        return HttpResponse(status=403, content="Dyspozycja nie istnieje.")


def show_vehicles(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    if driver.is_employed:
        employee = Employee.get_employee_by_driver_account(driver=driver)
        current_vehicle = Vehicle.get_vehicle_for_driver(employee=employee)
        if driver.has_speditor_permissions:
            vehicles = Vehicle.get_company_vehicles(company=employee.company, employee=employee)
    else:
        current_vehicle = Vehicle.get_vehicle_for_driver(driver=driver)
        vehicles = Vehicle.get_driver_vehicles(driver=driver)
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
    if driver.is_employed and driver.job_title == "owner" or driver.job_title == "speditor":
        if request.method == "POST":
            form = NewVehicleForm(request.POST)
            if form.is_valid():
                vehicle = form.save(commit=False)
                vehicle.company_owner = driver.company
                vehicle.photo = request.FILES.get("photo")
                vehicle.save()
                messages.success(request, "Pojazd został dodany poprawnie.")
                return redirect("/Company/Vehicles")
            else:
                messages.error(request, "Pojazd nie został dodany poprawnie. Powód: " + form.errors.as_json())
                return redirect("/Company/Vehicles")
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
    if driver.is_employed and driver.job_title == "owner" or driver.job_title == "speditor":
        vehicle = Vehicle.get_vehicle_from_id(vehicle_id)
        if vehicle:
            if request.method == "POST":
                form = EditVehicleForm(request.POST, instance=vehicle)
                if form.is_valid():
                    edited_vehicle = form.save(commit=False)
                    if request.FILES.get("photo"):
                        edited_vehicle.photo = request.FILES.get("photo")
                    if request.POST.get("owner"):
                        new_driver = Employee.get_employee_by_id(int(request.POST.get("owner")))
                        vehicle.driver_owner = new_driver
                    edited_vehicle.save()
                    messages.success(request, "Pojazd został edytowany poprawnie.")
                    return redirect("/Company/Vehicles")
                else:
                    messages.error(request, f"Pojazd nie został edytowany poprawnie. Powód: {form.errors}")
                    return redirect("/Company/Vehicles")
            else:
                employees = driver.company.drivers_list
                context = {
                    'form': EditVehicleForm(instance=vehicle),
                    'employees': employees,
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
    if not driver.is_employed:
        messages = Vehicle.change_selected_vehicle(driver, vehicle_id)
        if messages.get("error"):
            return HttpResponse(status=403, content="Pojazd nie istnieje.")
        return redirect("/vehicles")
    elif driver.is_employed and (driver.job_title == "owner" or driver.job_title == "speditor"):
        employee = Employee.get_employee_by_driver_account(driver)
        messages = Vehicle.change_selected_vehicle(employee=employee, vehicle_id=vehicle_id)
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
                messages.success(request, "Oferta została zaakceptowana poprawnie.")
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
                Employee.create_employee(driver, company, "owner")
                messages.success(request, f"Firma {company.name} została zarejestrowana. Powodzenia na wirtualnych szlakach!")
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
                messages.success(request, f"Aplikacja do firmy {company.name} została złożona poprawnie.")
                return redirect("/dashboard")
            else:
                messages.success(request, f"Aplikacja nie została złożona poprawnie. Powód: {form.errors}")
                return redirect("/dashboard")
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

def driver_deliveries(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    deliveries_list = Delivery.get_all_driver_deliveries(driver)
    if deliveries_list:
        paginator = Paginator(deliveries_list, 10)
        page = request.GET.get('page')

        try:
            deliveries = paginator.page(page)
        except PageNotAnInteger:
            deliveries = paginator.page(1)
        except EmptyPage:
            deliveries = paginator.page(paginator.num_pages)

    else:
        deliveries = None

    context = {
        "deliveries": deliveries,
        "deliveries_tag": "option--active",
        'is_employed': driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
    }

    return render(request, "driver_deliveries.html", context)


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
        return redirect('driver_deliveries')

def edit_delivery_details(request, delivery_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    try:
        delivery = Delivery.objects.get(id=delivery_id)
        if delivery.driver == driver:
            if request.method == "POST":
                form = EditDeliveryForm(request.POST, instance=delivery)
                if form.is_valid():
                    delivery.status = "Wysłana"
                    form.save()
                    messages.success(request, "Dostawa została edytowana poprawnie i oczekuje na zatwierdzenie przez spedycję.")
                return redirect("/Deliveries")
            else:
                disposition = Disposition.get_disposition_from_waybill(
                    driver=driver,
                    loading_city=delivery.loading_city,
                    unloading_city=delivery.unloading_city,
                    cargo=delivery.cargo,
                )
                context = {
                    'form': EditDeliveryForm(instance=delivery),
                    'disposition': disposition,
                    'add_new_delivery': 'option--active',
                    "is_employed": driver.is_employed,
                    "has_speditor_permissions": driver.has_speditor_permissions,
                }
                return render(request, "add_delivery_details.html", context)
        else:
            return HttpResponse(status=403, content="Nie posiadasz uprawnień do edycji tego zlecenia.")
    except Delivery.DoesNotExist:
        return HttpResponse(status=403, content="Dostawa nie istnieje.")


def show_delivery_details(request, delivery_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    if driver.is_employed and (driver.company and (driver.job_title == "owner" or driver.job_title == "speditor")) or not driver.is_employed:
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
                if delivery.driver == driver and driver.is_employed:
                    own_delivery = True
                else:
                    own_delivery = False

                context = {
                    'delivery': delivery,
                    'screenshots': screenshots,
                    'disposition': disposition,
                    'is_employed': driver.is_employed,
                    "has_speditor_permissions": driver.has_speditor_permissions,
                    'own_delivery': own_delivery,
                }

                return render(request, "delivery_details.html", context)
            else:
                return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
        except Delivery.DoesNotExist:
            return HttpResponse(status=404, content="Dostawa o podanym id nie została znaleziona.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")

def edit_delivery_status(request):
    if request.method == "POST":
        body = json.loads(request.body.decode("utf-8"))
        driver = Driver.get_driver_by_user_profile(request.user)
        if (driver.is_employed and (driver.company and (driver.job_title == "owner" or driver.job_title == "speditor"))) or not driver.is_employed:
            try:
                delivery_id = body.get("delivery_id")
                delivery = Delivery.get_delivery_by_id(delivery_id)
                if (delivery.driver.company == driver.company and delivery.driver != driver) or not driver.is_employed:
                    status = body.get("status")
                    reason = body.get("reason")
                    message = delivery.update_status(status, reason)
                    if not message.get("error"):
                        messages.success(request, "Dostawa rozpatrzona przez spedycję poprawnie.")
                        return HttpResponse(status=200, content={"is_employed": driver.is_employed})
                    else:
                        return HttpResponse(status=400, content="Błędny status dostawy.")
                else:
                    return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
            except ValueError:
                return HttpResponse(status=400, content="Błędne id dostawy.")
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
                    messages.success(request, "Profil kierowcy został edytowany poprawnie.")
                    return redirect("/Company/ManageDrivers")
                else:
                    return HttpResponse(content=form.errors)
            else:
                info = employee.get_driver_info()
                form = EditEmployeeForm(instance=employee)
                context = {
                    "info": info,
                    "employee_id": employee_id,
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


def dismiss_driver(request, employee_id):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    employee = Employee.get_employee_by_id(employee_id)
    if current_driver.is_employed:
        if current_driver.company and current_driver.job_title == "owner" and current_driver.company == employee.company:
            employee.dismiss_employee()
            messages.success(request, f"Kierowca został zwolniony poprawnie.")
            return redirect("/Company/ManageDrivers")
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def hire_driver(request):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    if current_driver.is_employed:
        if current_driver.company and current_driver.job_title == "owner":
            if request.method == "POST" and request.POST:
                form = AddEmployeeForm(request.POST)
                if form.is_valid():
                    new_employee = form.save(commit=False)
                    new_employee.save()
                    messages.success(request, f"Kierowca {new_employee.driver.nick} został zatrudniony do firmy.")
                    return redirect("/Company/ManageDrivers")
                else:
                    return HttpResponse(content=form.errors)
            else:
                vehicles = current_driver.company.get_free_vehicles()
                form = AddEmployeeForm()
                context = {
                    "manage_drivers": "option--active",
                    "is_employed": current_driver.is_employed,
                    "has_speditor_permissions": current_driver.has_speditor_permissions,
                    "form": form,
                    "vehicles": vehicles,
                }
            return render(request, "add_driver.html", context)
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def find_driver(request, nickname):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    if current_driver.is_employed:
        if current_driver.company and current_driver.job_title == "owner":
            if nickname:
                drivers = Driver.find_driver_by_nickname(nickname)
                if drivers:
                    return JsonResponse({'drivers': list(drivers)})
                else:
                    return JsonResponse({"message": "Nie znaleziono kierowców spełniających żądanie."})
            else:
                return HttpResponse(status=401, content="Nieprawidłowa nazwa użytkownika lub jej brak.")
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def show_company_vehicles(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    employee = Employee.get_employee_by_driver_account(driver)
    vehicles = Vehicle.get_company_vehicles(driver.company, employee)
    current_vehicle = Vehicle.get_vehicle_for_driver(employee=employee)
    context = {
        'current_vehicle': current_vehicle,
        'vehicles': vehicles,
        'vehicles_tag': "option--active",
        'is_employed': driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
    }
    return render(request, "vehicles.html", context)

def delete_vehicle(request, vehicle_id):
    driver = Driver.get_driver_by_user_profile(request.user)
    if driver.is_employed and driver.job_title == "owner":
        response = Vehicle.delete_vehicle(vehicle_id)
        if response.get("error"):
            return HttpResponse(status=401, content="Pojazd nie istnieje.")
        else:
            messages.success(request, "Pojazd został usunięty poprawnie.")
            return redirect("/Company/Vehicles")
    else:
        return HttpResponse(status=403, content="Nie masz uprawnień do usuwania pojazdu.")

def show_company_dispositions(request):
    driver = Driver.get_driver_by_user_profile(request.user)
    dispositions_list = Disposition.get_company_dispositions(driver.company)

    paginator = Paginator(dispositions_list, 7)
    page = request.GET.get('page')
    try:
        dispositions = paginator.page(page)
    except PageNotAnInteger:
        dispositions = paginator.page(1)
    except EmptyPage:
        dispositions = paginator.page(paginator.num_pages)
    context = {
        'dispositions': dispositions,
        'company_dispositions_tag': "option--active",
        'is_employed': driver.is_employed,
        "has_speditor_permissions": driver.has_speditor_permissions,
    }
    return render(request, "company_dispositions.html", context)

def company_preferences(request):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    if current_driver.is_employed:
        if current_driver.company and current_driver.job_title == "owner":
            if request.POST:
                form = EditCompanyForm(request.POST, instance=current_driver.company)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Ustawienia firmy zostały edytowane poprawnie.")
                    return redirect("/Company/Preferences")
            else:
                form = EditCompanyForm(instance=current_driver.company)
                context = {
                    'form': form,
                    'company_preferences': "option--active",
                    'is_employed': current_driver.is_employed,
                    "has_speditor_permissions": current_driver.has_speditor_permissions,
                }
                return render(request, "company_settings.html", context)
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")

def delete_company(request):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    if current_driver.is_employed:
        if current_driver.company and current_driver.job_title == "owner":
            current_driver.company.delete_company()
            messages.success(f"Firma została usunięta poprawnie.")
            return redirect("/dashboard")
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")

def show_company_applications(request):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    if current_driver.is_employed:
        if current_driver.company and current_driver.job_title == "owner":
            applications_list = EmployeeApplication.get_all_company_applications(current_driver.company)
            paginator = Paginator(applications_list, 10)
            page = request.GET.get('page')
            try:
                applications = paginator.page(page)
            except PageNotAnInteger:
                applications = paginator.page(1)
            except EmptyPage:
                applications = paginator.page(paginator.num_pages)
            context = {
                'applications': applications,
                'company_applications': "option--active",
                'is_employed': current_driver.is_employed,
                "has_speditor_permissions": current_driver.has_speditor_permissions,
            }
            return render(request, "company_applications.html", context)
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")

def check_application(request, application_id):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    if current_driver.is_employed:
        if current_driver.company and current_driver.job_title == "owner":
            application = EmployeeApplication.get_application_by_id(application_id)
            dlc = application.decode_dlc()
            if application:
                context = {
                    'application': application,
                    'dlc': dlc,
                    'company_applications': "option--active",
                    'is_employed': current_driver.is_employed,
                    "has_speditor_permissions": current_driver.has_speditor_permissions,
                }
            else:
                return HttpResponse(status=401, content="Nie znaleziono aplikacji o takim id.")
            return render(request, "application_details.html", context)
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def accept_application(request, application_id):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    if current_driver.is_employed:
        if current_driver.company and current_driver.job_title == "owner":
            application = EmployeeApplication.get_application_by_id(application_id)
            if application:
                application.accept_application()
                messages.success(request, "Podanie zostało zaakceptowane.")
                return redirect("/Company/Applications")
            else:
                return HttpResponse(status=401, content="Nie znaleziono aplikacji o takim id.")
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def reject_application(request, application_id):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    if current_driver.is_employed:
        if current_driver.company and current_driver.job_title == "owner":
            application = EmployeeApplication.get_application_by_id(application_id)
            if application:
                application.reject_application()
                messages.success(request, "Podanie zostało odrzucone.")
                return redirect("/Company/Applications")
            else:
                return HttpResponse(status=401, content="Nie znaleziono aplikacji o takim id.")
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")


def manage_disposition(request, disposition_id):
    current_driver = Driver.get_driver_by_user_profile(request.user)
    if current_driver.is_employed:
        if current_driver.company and (current_driver.job_title == "owner" or current_driver.job_title == "speditor"):
            disposition = Disposition.get_disposition_by_id(disposition_id)
            if request.method == "POST" and request.POST:
                form = EditDispositionForm(request.POST, instance=disposition)
                if form.is_valid():
                    edited_disposition = form.save(commit=False)
                    if request.POST.get("driver"):
                        employee_id = int(request.POST.get("driver"))
                        driver = Employee.get_employee_by_id(employee_id).driver
                        edited_disposition.driver = driver
                    if request.POST.get("deadline"):
                        edited_disposition.deadline = request.POST.get("deadline")
                    edited_disposition.save()
                    messages.success(request, "Dyspozycja została edytowana poprawnie.")
                    return redirect("/Company/Dispositions")
                else:
                    return HttpResponse(content=form.errors)
            else:
                form = EditDispositionForm(instance=disposition)
                employees = Employee.get_all_company_employees(current_driver.company)
                context = {
                    "company_dispositions_tag": "option--active",
                    'employees': employees,
                    "is_employed": current_driver.is_employed,
                    "has_speditor_permissions": current_driver.has_speditor_permissions,
                    "form": form,
                }
                return render(request, "manage_disposition.html", context)
        else:
            return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")
    else:
        return HttpResponse(status=403, content="Nie jesteś uprawniony do wykonania tej operacji.")