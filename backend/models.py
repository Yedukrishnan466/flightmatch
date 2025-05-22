from django.db import models
from django.contrib.auth.models import User

class FlightDetails(models.Model):
    flight_title = models.CharField(max_length=100, null=False, default="")
    flight_departure = models.TextField()
    flight_arrival = models.TextField()
    flight_duration = models.TextField()
    flight_price = models.TextField()
    flight_page_url = models.URLField(null=True, blank=True) # Optional field
    flight_image_url = models.URLField()
    fr_lc = models.CharField(max_length=20,null=True)
    to_lc = models.CharField(max_length=20,null=True)
    site_name = models.CharField(max_length=20,null=True)
    stop_type = models.CharField(max_length=20,null=True)
    free_meal = models.CharField(max_length=20,null=True)
    fl_sl_no = models.IntegerField(null=True, blank=True)
    fl_durat_num = models.IntegerField(null=True, blank=True)
    fl_price_num = models.IntegerField(null=True, blank=True)
    fl_dept_num = models.IntegerField(null=True, blank=True)

class FlightBooking(models.Model):
    trip_type = models.CharField(max_length=20)
    from_location = models.CharField(max_length=100)
    to_location = models.CharField(max_length=100)
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    traveller_details = models.TextField()  # Stores input like "2 Adults, 1 Children, 1 Infants, First Class"

    def __str__(self):
        return f"{self.from_location} → {self.to_location} ({self.traveller_details})"

class Airports(models.Model):
    airport_code = models.CharField(max_length=3)
    airport_name = models.CharField(max_length=100)
    airport_city = models.CharField(max_length=100)
    airport_country = models.CharField(max_length=100)
    airport_country_code = models.CharField(max_length=2)
    airport_search_element = models.CharField(max_length=100,null=True)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)