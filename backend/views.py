from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from .scraping import Search
from .urlbuilder import Url_constructor
import pandas as pd
import json
import datetime
from .DataScraperMIX import scrape_all_sites
from django.urls import reverse
from django.http import HttpResponseRedirect
# import db from model.py
from .models import FlightDetails, FlightBooking, Airports, Profile

# ty

# Create your views here.
def welcome(request):
    # clear all databases
    FlightDetails.objects.all().delete()
    FlightBooking.objects.all().delete()

    return render(request, 'welcome.html')

@never_cache
@login_required(login_url="/")
def home(request):
    if request.user.is_authenticated:  # Check if user is logged in
        username = request.user.username  # Get the logged-in user's username
        p_name = username[:2].upper()
    else:
        username = "Guest"
        p_name = "GU"  # Default for guests
    request.session['p_name'] = p_name
    # Flush all data out of FlightDetails table
    FlightDetails.objects.all().delete()
    #Prepare list of airports for search filtering in from and to fields
    airports = Airports.objects.all()
    ixigo_url = ""
    cleartrip_url = ""
    trip_url = ""

    if request.method == "POST":
        trip_type = request.POST.get("trip-type","one-way")
        from_city = request.POST.get("from_city", "")
        to_city = request.POST.get("to_city", "")
        departure_date = request.POST.get("departure_date", "")
        return_date = request.POST.get("return_date", "")
        traveller_details = request.POST.get("traveller_details", "")

        print("type:",trip_type,"\nfrom:",from_city,"\nto:",to_city,"\ndp_date:",departure_date,"\nrn_date:",return_date,"\ndetails:",traveller_details,"\n")

        # read fare-option from frontend post method to backend
        fare_option = request.POST.get("fare-option", "regular")
        print("Fare Option:", fare_option)

        # convert date to yyyy/mm/dd from dd/mm/yyyy
        departure_date_spl = departure_date.split("/")
        departure_date_ymd = departure_date_spl[2] + "-" + departure_date_spl[1] + "-" + departure_date_spl[0]
        print("Departure Date in YYYY-MM-DD format:", departure_date_ymd)

        # set condition for return date if exists
        if return_date:
            return_date_spl = return_date.split("/")
            return_date_ymd = return_date_spl[2] + "-" + return_date_spl[1] + "-" + return_date_spl[0]
        else:
            return_date_ymd = "2000-01-01"
        print("Return Date in YYYY-MM-DD format:", return_date_ymd)

        # json dump Airports db values into terminal using print
        # airports = Airports.objects.all().values()
        # print("Airports:", json.dumps(list(airports), indent=4))

        # from_city airport id
        fc = from_city
        # check presence of airport in db and find id
        airport = Airports.objects.filter(airport_search_element=fc).first()
        if airport:
            # get airport id
            f_id = airport.airport_code
        else:
            # if airport not found
            f_id = "Unknown"
        print("Departure Airport Code:", f_id)

        # to_city airport id
        tc = to_city
        # check presence of airport in db and find id
        airport = Airports.objects.filter(airport_search_element=tc).first()
        if airport:
            # get airport id
            t_id = airport.airport_code
        else:
            # if airport not found
            t_id = "Unknown"
        print("Arrival Airport Code:", t_id)
        # Save booking to the database
        booking = FlightBooking(
            from_location=from_city,
            to_location=to_city,
            departure_date=departure_date_ymd,
            return_date=return_date_ymd,
            traveller_details=traveller_details,
        )
        booking.save()

        # strip traveller_details into individual components adults, child, infants, class_type
        traveller_details = traveller_details.split(',')
        # adult
        adults = traveller_details[0].strip()[0]
        print("Adults : ",adults)
        # child
        child = traveller_details[1].strip()[0]
        print("Child : ",child)
        # infants
        infants = traveller_details[2].strip()[0]
        print("Infants : ",infants)
        
        # class_type
        class_type_details = traveller_details[3].strip().lower()
        print("Class Type : ",class_type_details)
        class_map = {
            "economy": "e",
            "business": "b",
            "first class": "f",
            "premium economy": "w"
        }
        class_type = class_map.get(class_type_details)  

        # convert date to a string without any /
        departure_date_str = departure_date.replace('/', '')

        # set condition for return date if exists
        if return_date:
            return_date_str = return_date.replace('/', '')
        else:
            return_date_str = "00000000"
                    
        # Pass data to the Search __init__(self, f_id, t_id, d_date, r_date, trip_type, adult, child, infant, class_type, special)
        search = Search(f_id, t_id, departure_date_str, return_date_str, trip_type, adults, child, infants, class_type, fare_option)
        search.build_url("ixigo")

        class_map = {
            "economy": "y",
            "business": "c",
            "first class": "f",
            "premium economy": "s"
        }
        class_type = class_map.get(class_type_details, "y")
        search = Url_constructor(f_id, t_id, departure_date_ymd, return_date_ymd, trip_type, adults, child, infants, class_type, fare_option)
        trip_url = search.build_url("trip")

        # check if both airports in same country using airports db and airport country
        airport1 = Airports.objects.get(airport_code=f_id)
        airport2 = Airports.objects.get(airport_code=t_id)
        if airport1.airport_country == airport2.airport_country:
            # if same country then set intl as n
            intl="n"
        else:
            # if different country then set intl as y
            intl="y"

        # class_type needs to be converted for e its Economy
        class_type_details = traveller_details[3].lower()
        class_map = {
            "economy": "Economy",
            "business": "Business",
            "first class": "First",
            "premium economy": "Premium"
        }
        class_type = class_map.get(class_type_details, "Economy")

        # set departure and return dates in format DD/MM/YYYY
        """departure_date_spl = departure_date.split("/")
        departure_date_c = departure_date_spl[0] + "/" + departure_date_spl[1] + "/" + departure_date_spl[2]
        print(departure_date_c)
        if return_date:
            return_date_spl = return_date.split("/")
            return_date_c = return_date_spl[0] + "/" + return_date_spl[1] + "/" + return_date_spl[2]
        else:
            return_date_c = "00000000"
        print(return_date_c)"""

        date_obj = datetime.datetime.strptime(departure_date, "%d/%m/%Y")
        departure_date_ymd = date_obj.strftime("%Y-%m-%d")
        departure_date_c = date_obj.strftime("%d/%m/%Y")
        if return_date:
            date_obj = datetime.datetime.strptime(return_date, "%d/%m/%Y")
            return_date_ymd = date_obj.strftime("%Y-%m-%d")
            return_date_c = date_obj.strftime("%d/%m/%Y")
        else:
            return_date_ymd = "00000000"
            return_date_c = "00000000"

        search = Url_constructor(f_id, t_id, departure_date_c, return_date_c, trip_type, adults, child, infants, class_type, fare_option, intl)
        cleartrip_url = search.build_url("cleartrip")
        print(ixigo_url)
        print(cleartrip_url)
        print(trip_url)
        scrape_all_sites(trip_url,f_id, t_id)
        return redirect('results')

    return render(request, "home.html",{"p_name": p_name, "airports": airports})  # Render homepage normally


@never_cache
@login_required
def results(request):
    p_name = request.session.get('p_name', "GU")
    sort_by = request.GET.get("sort_by", "best")

    # Filters from URL
    selected_stops = request.GET.getlist("stops")           # e.g., ['non-stop', '1-stop']
    selected_food = request.GET.getlist("food")             # e.g., ['free_meal']
    selected_departure_range = request.GET.get("departure_range")  # e.g., "before_6", "6_12", etc.

    # Start with all flights
    flights = FlightDetails.objects.all()

    # Apply Stop filter
    if selected_stops:
        flights = flights.filter(stop_type__in=selected_stops)

    # Apply Food filter
    if 'free_meal' in selected_food:
        flights = flights.filter(free_meal__icontains="Free")

    # Apply Departure Time filter (based on fl_dept_num like 545, 1130, etc.)
    if selected_departure_range == "before_6":
        flights = flights.filter(fl_dept_num__lt=600)
    elif selected_departure_range == "6_12":
        flights = flights.filter(fl_dept_num__gte=600, fl_dept_num__lt=1200)
    elif selected_departure_range == "12_18":
        flights = flights.filter(fl_dept_num__gte=1200, fl_dept_num__lt=1800)
    elif selected_departure_range == "after_18":
        flights = flights.filter(fl_dept_num__gte=1800)

    # Sorting logic
    if sort_by == "price":
        flights = flights.order_by("fl_price_num")
    elif sort_by == "fastest":
        flights = flights.order_by("fl_durat_num")
    elif sort_by == "departure":
        flights = flights.order_by("fl_dept_num")
    else:
        flights = flights.order_by("fl_sl_no")

    return render(request, "results.html", {
        "p_name": p_name,
        "flights": flights,
        "sort_by": sort_by,
        "selected_stops": selected_stops,
        "selected_food": selected_food,
        "selected_departure_range": selected_departure_range,
    })

     

@never_cache
@login_required
def about(request):
    p_name = request.session.get('p_name', "GU")
    return render(request, 'about.html',{"p_name": p_name})

@never_cache
@login_required
def contact(request):
    p_name = request.session.get('p_name', "GU")
    return render(request, 'contact.html',{"p_name": p_name})

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            user = authenticate(request, username=username, password=password)

            if user is None:
                return JsonResponse({"status": "error", "message": "Invalid password"})
            else:
                login(request, user)
                return render(request, 'loading.html')  # Delay before redirecting to home

    return render(request, 'signin.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if User.objects.filter(username=username).exists():
            return JsonResponse({"status": "error", "message": "Username already exists"})
        elif User.objects.filter(email=email).exists():
            return JsonResponse({"status": "error", "message": "Email already exists"})
        elif password != confirm_password:
            return JsonResponse({"status": "error", "message": "Passwords do not match"})
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            user = authenticate(request, username=username, password=password)
            login(request, user)
            return render(request, 'loading.html')  # Delay before redirecting to home

    return render(request, 'signup.html')


def h_about(request):
    return render(request, 'h_about.html')

def h_contact(request):
    return render(request, 'h_contact.html')
def pr(request):
    return render(request, 'pr.html')    
def tnc(request):
    return render(request, 'tnc.html')       

def logout_view(request):
    print("Logout Initiated")

    logout(request)

    # Remove the user's session data by setting all keys to None
    request.session.flush()

    if request.user.is_authenticated:
        # User is logged in
        print("Authenticated")
    else:
        # User is logged out
        print("Not Authenticated")

    return redirect('welcome')