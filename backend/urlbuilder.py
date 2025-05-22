from .models import FlightDetails
from urllib.parse import urlencode
class Url_constructor:
    def __init__(self, f_id, t_id, d_date, r_date, trip_type, adult, child, infant, class_type, special, intl=""):
        self.f_id = f_id
        self.t_id = t_id
        self.d_date = d_date
        self.r_date = r_date
        self.trip_type = trip_type
        self.adult = adult
        self.child = child
        self.infant = infant
        self.class_type = class_type
        self.special = special
        self.intl = intl

    def build_url(self, site):
        if site == "ixigo":
            base_url = "https://www.ixigo.com/search/result/flight"
            params = {
                "from": self.f_id,
                "to": self.t_id,
                "date": self.d_date,
                "adults": self.adult,
                "children": self.child,
                "infants": self.infant,
                "class": self.class_type,
                "source": "Search Form",
                "airlineFareType": self.special,
                "hbs": "true"
            }
            if self.trip_type == "round-trip":
                params["returnDate"] = self.r_date
            url = base_url + "?" + urlencode(params)
            return url

        elif site == "trip":
            # https://in.trip.com/flights/showfarefirst?dcity=del&acity=lko&ddate=2025-04-05&triptype=ow&class=y&quantity=1&childqty=1&babyqty=1
            base_url = "https://in.trip.com/flights/showfarefirst"
            params = {
                "dcity": self.f_id.lower(),
                "acity": self.t_id.lower(),
                "ddate": self.d_date,
                "triptype": "ow",
                "class": self.class_type.lower(),
                "quantity": self.adult,
                "childqty": self.child,
                "babyqty": self.infant
            }
            # https://in.trip.com/flights/showfarefirst?dcity=del&acity=lko&ddate=2025-04-05&rdate=2025-04-08&triptype=rt&class=y&quantity=1

            if self.trip_type == "round-trip":
                params["triptype"] = "rt"
                params["rdate"] = self.r_date
            url = base_url + "?" + urlencode(params)
            return url

        elif site == "cleartrip":
            # https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&class=Economy&depart_date=10/04/2025&from=DEL&to=LKO&intl=n&rnd_one=O
            base_url = "https://www.cleartrip.com/flights/results"
            params = {
                "adults": self.adult,
                "childs": self.child,
                "infants": self.infant,
                "class": self.class_type,
                "depart_date": self.d_date,
                "intl": self.intl,
                "from": self.f_id,
                "to": self.t_id,
            }
            if self.trip_type == "one-way":
                params["rnd_one"] = "O"
            # https://www.cleartrip.com/flights/results?adults=1&childs=0&infants=0&depart_date=10/04/2025&return_date=11/04/2025&intl=n&from=DEL&to=LKO&class=Economy
            elif self.trip_type == "round-trip":
                params["return_date"] = self.r_date
    
            url = base_url + "?" + urlencode(params)
            return url