from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from .models import FlightDetails
import json
import time
import logging
from urllib.parse import urlencode

# ty

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ChromeSource:
    def getSource(self, url):
        options = Options()
        options.add_argument('headless')
        options.add_argument('log-level=3')
        options.add_argument("user-agent=Mozilla/5.0")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(10)

        try:
            driver.execute_script("document.body.style.zoom='0.1%'")
        except Exception as e:
            logging.error(f"Zoom adjustment failed: {e}")
        
        # Wait for flight listings to load
        """try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, flight_listing))
            )
        except Exception as e:
            logging.warning(f"Error waiting for flight listings: {e}")
        """
        retval = driver.page_source
        driver.quit()
        return retval

class Search:
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

        logging.info(f"Constructed URL: {url}")
        scrape = ScrapeFlights(url, site, self.f_id, self.t_id)
        scrape.scraping_parameters(url, site)

class ScrapeFlights:
    def __init__(self, url, site, f_id, t_id):
        self.url = url
        self.site = site
        self.f_id = f_id
        self.t_id = t_id

    def scraping_parameters(self, url, site):
        if site == "ixigo":
            self.flight_listing = "shadow-[0px_2px_5px_0px_rgba(0,0,0,0.10)]"
            self.flight_title = "airlineTruncate"
            self.flight_price = "h6 text-primary font-bold"
            self.flight_duration = "body-sm text-secondary"
            self.flight_departure = "h6 text-primary font-medium"
            self.stop_type = "body-sm text-secondary"

        elif site == "trip":
            self.flight_listing = "f-info-content is-v2"
            self.flight_title = "flights-name"
            self.flight_logo = "flight-info-airline__logo airline-logo"
            self.flight_price = "ThemeColor8 f-20 o-price-flight_b825 no-cursor_1b76"
            self.flight_duration = [
                "flightinfoduration",
                "flight-info-duration_576d",
            ]
            self.flight_departure = "flight-info-airline__timers_39aa"

        elif site == "cleartrip":
            self.flight_listing = "ba bc-neutral-100 br-12 p-4 tp-box-shadow td-200 p-relative intl-tuple ow-tuple-container--intl pt-1 hover:elevation-3"
            self.flight_title = "fs-4 fw-500 c-white"
            self.flight_price = "m-0 fs-6 fw-600 c-neutral-900 ws-nowrap h-7"
            self.flight_duration = "c-white fs-2 fw-500"
            self.flight_departure = "fs-7 fw-500 c-white"
        

        self.url = url
        self.scrapeSearchResults()

    def scrapeSearchResults(self):
        output = []

        logging.info("Extracting flight details from page")
        data = self.extractFlightDetails()
        if not data:
            logging.warning("No flight details found.")
            return
        i=1
        for inp in range(len(data)):
            flight = data[inp]
            logging.info(f"Scraping individual flight details: {flight['title']}")

            flight_data = {
                "Title": flight['title'],
                "Airline Logo": flight["airline_logo"],
                "Departure Time": flight["departure"],
                "Arrival Time": flight["arrival"],
                "Duration": flight["duration"],
                "Price": flight["price"],
                "Stop_type": flight["stop_type"],
                "Free_Meal": flight["free_meal"],
            }
            duration = flight["duration"]  # e.g., "3h 25m"
            hours = 0
            minutes = 0

            if 'h' in duration:
                hours = int(duration.split('h')[0].strip())
                duration = duration.split('h')[1]

            if 'm' in duration:
                minutes = int(duration.split('m')[0].strip())

            dur_num = hours * 60 + minutes

            departure_time = flight["departure"]  # e.g., "19:15"
            dept_num = int(departure_time.replace(":", ""))  
            price_str = flight["price"]  # e.g., "Rs.3,608"
            price_num = int(price_str.replace("Rs.", "").replace(",", "").strip()) 
            # Store the flight data into FlightDetails table
            flight_details_db = FlightDetails(
                flight_title = flight['title'],
                flight_departure = flight["departure"],
                flight_arrival = flight["arrival"],
                flight_duration = flight["duration"],
                flight_price = flight["price"],
                flight_page_url = self.url,
                flight_image_url = flight['airline_logo'],
                site_name = "ixigo.com",
                stop_type = flight["stop_type"],
                fr_lc = self.f_id,
                to_lc = self.t_id,
                free_meal = flight["free_meal"],
                fl_sl_no = i,
                fl_durat_num = dur_num,
                fl_price_num = price_num,
                fl_dept_num = dept_num
            )
            flight_details_db.save()

            output.append(flight_data)
            print(i)
            print(dur_num)
            print(price_num)
            print(dept_num)
            i=i+2
        
        logging.info(json.dumps(output, indent=4))

    def extractFlightDetails(self):
        logging.info("Extracting each flight details")
        chrome_source = ChromeSource()
        soup = bs(chrome_source.getSource(self.url), 'lxml')

        # Extracting flight details from ixigo
        if self.site == "ixigo":
            ixigo = []
            flight_details = soup.find_all('div', class_=self.flight_listing)
            if not flight_details:
                logging.warning("No flight listings found. Check the class name for flight listings.")
                return ixigo

            for flight in flight_details:
                try:
                    flight_name = flight.find('p', class_=self.flight_title).text.strip()
                    airline_logo = flight.find('img', {'data-testid': 'airline-logo'})
                    airline_logo_url = airline_logo['src'] if airline_logo else "N/A"
                    free_meal_logo = flight.find('img', {'alt':'Free Meal'})
                    free_meal = "Free Meal" if free_meal_logo else ""
                    times = flight.find_all('h6', class_=self.flight_departure)
                    departure_time = times[0].get_text(strip=True) if times else "N/A"
                    arrival_time = times[1].get_text(strip=True) if len(times) > 1 else "N/A"
                    duration_elements = flight.find_all('p', class_=self.flight_duration)
                    duration = duration_elements[1].text.strip() if len(duration_elements) > 0 else "N/A"
                    stop_type = duration_elements[2].text.strip() if len(duration_elements) > 1 else "N/A"
                    price = flight.find('h6', class_=self.flight_price).text.strip().replace("\u20b9","Rs.") if flight.find('h6', class_=self.flight_price) else "N/A"

                    ixigo.append({
                        "title": flight_name,
                        "airline_logo": airline_logo_url,
                        "departure": departure_time,
                        "arrival": arrival_time,
                        "duration": duration,
                        "price": price,
                        "stop_type": stop_type,
                        "free_meal": free_meal
                    })

                except Exception as e:
                    logging.error(f"Error extracting flight details: {e}")
                    continue
            return ixigo
        
        # Extracting flight details from trip
        elif self.site == "trip":
            trip = []
            flight_details = soup.find_all('div', class_=self.flight_listing)
            if not flight_details:
                logging.warning("No flight listings found. Check the class name for flight listings.")
                return trip
            for flight in flight_details:
                try:
                    flight_name = flight.find('div', class_=self.flight_title).text.strip()
                    # scrape airline logo from img src
                    airline_logo = flight.find('img', class_=self.flight_logo)
                    airline_logo_url = airline_logo['src'] if airline_logo else "N/A"
                    times = flight.find_all('div', class_=self.flight_departure)
                    departure_time = times[0].get_text(strip=True) if times else "N/A"
                    arrival_time = times[1].get_text(strip=True) if len(times) > 1 else "N/A"
                    duration = flight.find('div', class_=self.flight_duration[0]).text.strip()+flight.find('div', class_=self.flight_duration[1]).text.strip()
                    price = flight.find('span', class_=self.flight_price).text.strip()
                    
                    trip.append({
                        "title": flight_name,
                        "airline_logo": airline_logo_url,
                        "departure": departure_time,
                        "arrival": arrival_time,
                        "duration": duration,
                        "price": price
                    })
                except Exception as e:
                    logging.error(f"Error extracting flight details: {e}")
                    continue
            return trip

        # Extracting flight details from cleartrip
        elif self.site == "cleartrip":
            cleartrip = []
            flight_details = soup.find_all('div', class_=self.flight_listing)
            if not flight_details:
                logging.warning("No flight listings found. Check the class name for flight listings.")
                return cleartrip
            for flight in flight_details:
                try:
                    flight_name = flight.find('p', class_=self.flight_title).text.strip()
                    airline_logo = flight.find('img', {'data-testid': 'airline-logo'})
                    airline_logo_url = airline_logo['src'] if airline_logo else "N/A"
                    times = flight.find_all('p', class_=self.flight_departure)
                    departure_time = times[0].text.strip() if times else "N/A"
                    arrival_time = times[1].text.strip() if len(times) > 1 else "N/A"
                    duration = flight.find('p', class_=self.flight_duration).text.strip() if flight.find_all('p', class_=self.flight_duration)[1] else "N/A"
                    price = flight.find('p', class_=self.flight_price).text.strip().replace("\u20b9","Rs.") if flight.find('h6', class_=self.flight_price) else "N/A"
                    
                    cleartrip.append({
                        "title": flight_name,
                        "airline_logo": airline_logo_url,
                        "departure": departure_time,
                        "arrival": arrival_time,
                        "duration": duration,
                        "price": price
                    })
                except Exception as e:
                    logging.error(f"Error extracting flight details: {e}")
                    continue
            return cleartrip


