from typing import Dict, Any
from uuid import uuid4
from random import randrange
import os
import json
from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User
from django.conf import settings as django_settings




class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nick = models.CharField(max_length=128)
    avatar = models.ImageField(upload_to='avatars')

    @property
    def is_employed(self):
        try:
            Employee.objects.get(driver=self)
            return True
        except Employee.DoesNotExist:
            return False

    @property
    def company(self):
        if self.is_employed:
            return Employee.objects.get(driver=self).company.name
        return None

    @property
    def job_title(self):
        if self.is_employed:
            return Employee.objects.get(driver=self).job_title
        return None

    @property
    def distance(self):
        distance = Delivery.objects.filter(driver=self, is_edited=False).aggregate(Sum('distance'))
        return distance

    @property
    def tonnage(self):
        tonnage = Delivery.objects.filter(driver=self, is_edited=False).aggregate(Sum('tonnage'))
        return tonnage

    @property
    def deliveries_count(self):
        deliveries_count = Delivery.objects.filter(driver=self, is_edited=False).count()
        return deliveries_count

    @property
    def total_income(self):
        total_income = Delivery.objects.filter(driver=self, is_edited=False).aggregate(Sum('income'))
        return total_income

    def get_statistics(self):
        statistics: dict[str, int] = {
            'distance': self.distance,
            'tonnage': self.tonnage,
            'deliveries_count': self.deliveries_count,
            'income': self.total_income
        }
        return statistics

    def get_driver_info(self):
        info: dict[Any, Any] = {
            'avatar': self.avatar,
            'nick': self.nick,
            'statistics': self.get_statistics(),
            'disposition': Disposition.get_disposition_for_driver(self),
            'vehicle': Vehicle.get_vehicle_for_driver(self),
            'last_deliveries': Delivery.get_last_deliveries_for_driver(self),
        }
        return info

    @staticmethod
    def get_driver_by_user_profile(user: User):
        driver = Driver.objects.get(user=user)
        return driver

    def __str__(self):
        return self.nick


class Company(models.Model):
    name = models.CharField(max_length=128)
    logo = models.ImageField(upload_to='logos')
    is_recruiting = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    @property
    def drivers_count(self):
        return Employee.objects.filter(company=self).count()

    @property
    def company_vehicles(self):
        return


class Employee(models.Model):
    JOB_TITLES = (
        ('Właściciel', 'owner'),
        ('Szef', 'boss'),
        ('Spedytor', 'speditor'),
        ('Kierowca', 'driver')
    )

    driver = models.OneToOneField(Driver, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=64, choices=JOB_TITLES, default="Kierowca")


class Vehicle(models.Model):
    MANUFACTURERS = (
        ('MAN', 'man'),
        ('Mercedes-Benz', 'mercedes'),
        ('Scania', 'scania'),
        ('Volvo', 'volvo'),
        ('DAF', 'daf'),
        ('Renault', 'renault'),
        ('IVECO', 'iveco'),
    )

    manufacturer = models.CharField(max_length=24, choices=MANUFACTURERS)
    driver = models.OneToOneField(Driver, null=True, blank=True, on_delete=models.SET_NULL)
    model = models.CharField(max_length=64)
    photo = models.ImageField(upload_to='vehicles')
    cabin = models.CharField(max_length=10)
    engine = models.PositiveSmallIntegerField(default=0)
    chassis = models.CharField(max_length=3, default="4x2")
    odometer = models.PositiveIntegerField(default=0)
    license_plate = models.CharField(max_length=10)
    is_drawed = models.BooleanField(default=False)
    company_owner = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    driver_owner = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True, related_name="driver_owner")

    @staticmethod
    def get_vehicle_for_driver(driver: Driver):
        try:
            vehicle = Vehicle.objects.get(driver=driver, driver_owner=driver)
            return vehicle
        except Vehicle.DoesNotExist:
            return None

    @staticmethod
    def get_driver_vehicles(driver: Driver):
        try:
            vehicle = Vehicle.objects.filter(driver=None, driver_owner=driver)
            return vehicle
        except Vehicle.DoesNotExist:
            return None


class Delivery(models.Model):
    DELIVERY_STATUS = (
        ('Zaakceptowana', 'accepted'),
        ('Do poprawy', 'edit'),
        ('Odrzucona', 'rejected'),
        ('Wysłana', 'sent')
    )

    delivery_key = models.UUIDField(default=uuid4, editable=False)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    loading_city = models.CharField(max_length=128)
    unloading_city = models.CharField(max_length=128)
    loading_spedition = models.CharField(max_length=128, blank=True)
    unloading_spedition = models.CharField(max_length=128, blank=True)
    cargo = models.CharField(max_length=64)
    tonnage = models.PositiveSmallIntegerField(default=0)
    fuel = models.PositiveSmallIntegerField(default=0)
    distance = models.PositiveSmallIntegerField(default=0)
    income = models.PositiveIntegerField(default=0)
    damage = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=16, choices=DELIVERY_STATUS, default="Wysłana")
    is_edited = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def get_last_deliveries_for_driver(driver: Driver):
        deliveries = []
        accepted = Delivery.objects.filter(driver=driver, status='Zaakceptowana', is_edited=False).order_by("-created_at")
        sent = Delivery.objects.filter(driver=driver, status='Wysłana', is_edited=False).order_by("-created_at")
        to_edit = Delivery.objects.filter(driver=driver, status='Do poprawy', is_edited=False).order_by("-created_at")
        rejected = Delivery.objects.filter(driver=driver, status='Odrzucona', is_edited=False).order_by("-created_at")
        if rejected:
            deliveries.append(rejected)
        if to_edit:
            deliveries.append(to_edit)
        if sent:
            deliveries.append(sent)
        if accepted:
            deliveries.append(accepted)
        return deliveries


class DeliveryScreenshot(models.Model):
    delivery = models.ForeignKey(Delivery, default=None, on_delete=models.CASCADE)
    screenshot = models.ImageField(upload_to="waybills/")

    @staticmethod
    def get_screenshots(delivery):
        return DeliveryScreenshot.objects.filter(delivery=delivery)

    @staticmethod
    def process_screenshots(user, screenshots):
        driver = Driver.get_driver_by_user_profile(user)
        delivery = Delivery.objects.create(driver=driver)
        if len(screenshots) == 1:
            DeliveryScreenshot.objects.create(
                delivery=delivery,
                screenshot=screenshots.get("file"),
            )
        elif len(screenshots) > 1:
            for i in range(len(screenshots)):
                DeliveryScreenshot.objects.create(
                    delivery=delivery,
                    screenshot=screenshots.get(f"file[{i}]")
                )
        return delivery.delivery_key


class Offer(models.Model):
    TRAILERS = (
        ('Plandeka', 'curtain'),
        ('Chłodnia', 'reefer'),
        ('Niskopodłogowa', 'flatbed'),
        ('Kłonicowa', 'logger'),
        ('Wywrotka', 'tipper'),
        ('Kontener', 'container')
    )

    loading_city = models.CharField(max_length=128)
    unloading_city = models.CharField(max_length=128)
    loading_spedition = models.CharField(max_length=128)
    unloading_spedition = models.CharField(max_length=128)
    cargo = models.CharField(max_length=64)
    tonnage = models.PositiveSmallIntegerField(default=0)
    income = models.PositiveIntegerField(default=0)
    trailer = models.CharField(max_length=16, choices=TRAILERS)
    created_at = models.DateTimeField(auto_now_add=True)


class Disposition(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    loading_city = models.CharField(max_length=128)
    unloading_city = models.CharField(max_length=128)
    loading_spedition = models.CharField(max_length=128, blank=True)
    unloading_spedition = models.CharField(max_length=128, blank=True)
    cargo = models.CharField(max_length=64)
    tonnage = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
    is_accepted = models.BooleanField(default=False)

    def change_accept(self):
        try:
            disposition = Disposition.objects.get(driver=driver, is_accepted=True)
            return "Istnieje już zaakceptowana dyspozycja! Ukończ ją przed akceptacją drugiej."
        except Disposition.DoesNotExist:
            self.is_accepted = True

    @staticmethod
    def generate_disposition(driver: Driver, data: Dict):
        cities_file = open(os.path.join(django_settings.STATIC_ROOT, 'files/cities.json'), "r", encoding="UTF-8")
        cities = json.loads(cities_file.read())
        cities_file.close()

        try:
            if data.get("auto-loading-city"):
                last_accepted_waybill = Delivery.objects.order_by("-accepted_at").first()
                for json_city in cities["response"]:
                    if json_city.get("realName") == last_accepted_waybill.unloading_city:
                        loading_city = json_city
                        break
                if not loading_city:
                    print(f"Error: {loading_city} not found in cities list.")
                    return None
            else:
                loading_country = data.get("loading_country")
                unloading_country = data.get("unloading_country")
                if loading_country != "random":
                    loading_cities = []
                    for json_city in cities["response"]:
                        if json_city.get("country") == loading_country:
                            #If there isn't promods checked, we need only no-promods cities
                            if not "promods" in data.get("modification"):
                                if json_city.get("mod") != "promods":
                                    loading_cities.append(json_city)
                            #if not, all cities within country are ok
                            else:
                                loading_cities.append(json_city)
                    loading_city_number = randrange(0, len(loading_cities))
                    loading_city = loading_cities[loading_city_number]
                else:
                    if "promods" in data.get("modification"):
                        loading_city_number = randrange(0, 564)
                    else:
                        loading_city_number = randrange(0, 279)
                    loading_city = cities["response"][loading_city_number]

            if unloading_country != "random":
                unloading_cities = []
                for json_city in cities["response"]:
                    if json_city.get("country") == unloading_country:
                        if "promods" in data.get("modification") and json_city.get("mod") == "promods":
                            unloading_cities.append(json_city)
                        elif not "promods" in data.get("modification") and json_city.get("mod") != "promods":
                            unloading_cities.append(json_city)
                unloading_city_number = randrange(0, len(unloading_cities))
                unloading_city = unloading_cities[unloading_city_number]
            else:
                if "promods" in data.get("modification"):
                    unloading_city_number = randrange(0, 564)
                else:
                    unloading_city_number = randrange(0, 279)
                unloading_city = cities["response"][unloading_city_number]

            try:
                loading_companies_count = len(loading_city.get("companies")) - 1
                loading_spedition_number = randrange(0, loading_companies_count)
                loading_spedition = loading_city["companies"][loading_spedition_number]

            except TypeError:
                print(f"{loading_city} has no companies. Refer to cities.json file.")
                loading_spedition = "Dowolna"

            try:
                unloading_companies_count = len(unloading_city.get("companies")) - 1
                unloading_spedition_number = randrange(0, unloading_companies_count)
                unloading_spedition = unloading_city["companies"][unloading_spedition_number]

            except TypeError:
                print(f"{unloading_city} has no companies. Refer to cities.json file.")
                unloading_spedition = "Dowolna"
        except IndexError:
            return None

        Disposition.objects.create(
            driver = driver,
            loading_city = loading_city.get("realName"),
            loading_spedition = loading_spedition,
            unloading_city = unloading_city.get("realName"),
            unloading_spedition = unloading_spedition,
            cargo = "test",
            tonnage = "22",
            deadline = "2022-02-17 13:50"
        )
        return True

    @staticmethod
    def get_disposition_for_driver(driver: Driver):
        try:
            disposition = Disposition.objects.get(driver=driver, is_accepted=True)
            return disposition
        except Disposition.DoesNotExist:
            return None

    @staticmethod
    def get_unaccepted_dispositions(driver: Driver):
        try:
            dispositions = Disposition.objects.filter(driver=driver, is_accepted=False)
            return dispositions
        except Disposition.DoesNotExist:
            return None

    @staticmethod
    def get_disposition_from_waybill(driver: Driver,
                                     loading_city: str,
                                     unloading_city: str,
                                     cargo: str):
        try:
            disposition = Disposition.objects.get(driver=driver,
                                                  loading_city=loading_city,
                                                  unloading_city=unloading_city,
                                                  cargo=cargo)
            return disposition
        except Disposition.DoesNotExist:
            return None


class VehicleBorrow(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()
