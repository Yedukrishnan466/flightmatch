import logging
import re
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import datetime
from .models import FlightDetails


def filter_departure_time(time_str):
    """
    Filters the input departure time string to capture only the hh:mm format.
    If such a pattern is found, returns it; otherwise, returns "N/A".
    """
    match = re.search(r"\b\d{1,2}:\d{2}\b", time_str)
    if match:
        return match.group(0)
    return "N/A"


class ChromeSource:
    def get_source(self, url):
        logging.info(f"Opening URL: {url}")
        options = Options()
        options.add_argument("headless")
        options.add_argument("log-level=3")
        options.add_argument("user-agent=Mozilla/5.0")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )

        driver.get(url)
        time.sleep(5)  # Wait for page to load
        # SCROLL TO LOAD ALL FLIGHTS
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for more flights to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Now the full content is loaded
        page_source = driver.page_source
        driver.quit()
        return page_source
        
        try:
            driver.execute_script("document.body.style.zoom='0.1%'")
        except Exception as e:
            logging.error(f"Zoom adjustment failed: {e}")

        page_source = driver.page_source
        driver.quit()
        return page_source


class FlightScraper:
    def __init__(self, url, site_name, selectors):
        self.url = url
        self.site_name = site_name
        self.selectors = selectors

    def extract_flight_details(self):
        logging.info(f"Scraping {self.site_name}")
        source = ChromeSource().get_source(self.url)
        soup = bs(source, "lxml")
        flights = soup.find_all("div", class_=self.selectors["flight_listing"])

        if not flights:
            logging.warning(
                f"No flights found for {self.site_name}. Check class names."
            )

        results = []
        for flight in flights:
            try:
                if self.site_name == "Ixigo":
                    title_elem = flight.find("p", class_=self.selectors["flight_title"])
                    departure_elems = flight.find_all(
                        "h6", class_=self.selectors["flight_departure"]
                    )
                    duration_elems = flight.find_all(
                        "p", class_=self.selectors["flight_duration"]
                    )
                    price_elem = flight.find(
                        "h6", class_=self.selectors["flight_price"]
                    )

                elif self.site_name == "Trip":
                    title_elem = flight.find(
                        "div", class_=self.selectors["flight_title"]
                    )
                    departure_elems = flight.find_all(
                        "div", class_=self.selectors["flight_departure"]
                    )
                    # Handle multiple possible duration classes
                    duration_elems = []
                    for class_name in self.selectors["flight_duration"]:
                        duration_elems += flight.find_all("div", class_=class_name)
                    price_elem = flight.find(
                        "span", class_=self.selectors["flight_price"]
                    )
                    image_elem = flight.find(
                        "img", class_=self.selectors["flight_image"]
                    )
                    free_meal_elem = flight.find(
                        "i", {'class':'fi-icon fi-icon_dinner_new comfort-icon-item'}
                    )    

                elif self.site_name == "Cleartrip":
                    title_elem = flight.find("p", class_=self.selectors["flight_title"])
                    departure_elems = flight.find_all(
                        "p", class_=self.selectors["flight_departure"]
                    )
                    duration_elems = flight.find_all(
                        "p", class_=self.selectors["flight_duration"]
                    )
                    price_elem = flight.find("p", class_=self.selectors["flight_price"])

                # Extract values for title, departure, and arrival
                title = title_elem.text.strip() if title_elem else "N/A"
                departure = (
                    departure_elems[0].text.strip()
                    if len(departure_elems) > 0
                    else "N/A"
                )
                arrival = (
                    departure_elems[1].text.strip()
                    if len(departure_elems) > 1
                    else "N/A"
                )

                # Extract duration and then filter out extra stop details.
                # Join all duration elements into one string.
                duration_full = (
                    ", ".join([elem.text.strip() for elem in duration_elems])
                    if duration_elems
                    else "N/A"
                )
                # Updated regex: allow optional minutes (i.e. "15h" or "15h 40m")
                match = re.search(r"(\d+\s*h(?:\s*\d+\s*m)?)", duration_full, re.I)
                if match:
                    duration = match.group(1)
                else:
                    duration = duration_full

                # Extract price
                price = (
                    price_elem.text.strip().replace("\u20b9", "Rs.")
                    if price_elem
                    else "N/A"
                )

                image_url = "N/A"
                if image_elem and image_elem.get("src"):
                    image_url = "https:"+str(image_elem["src"])
                    #	https://static.tripcdn.com/packages/flight/airline-logo/latest/airline_logo/3x/6e.webp
                free_meal = ""
                if free_meal_elem:
                    free_meal = "Free Meal"

                logging.info(
                    f"Extracted: {title}, Departure: {departure}, Arrival: {arrival}, Duration: {duration}, Price: {price}"
                )
                results.append(
                    [title, departure, arrival, duration, price, self.site_name, image_url,free_meal]
                )
            except Exception as e:
                logging.error(f"Error extracting details: {e}")

        return pd.DataFrame(
            results,
            columns=["Title", "Departure", "Arrival", "Duration", "Price", "Site","Image_URL","Free_Meal"],
        )


def scrape_all_sites(trip_url, f_id, t_id):

    urls = {
        #"Ixigo": ixigo_url,
        "Trip": trip_url,
        #"Cleartrip": cleartrip_url,
    }

    selectors = {
        "Ixigo": {
            "flight_listing": "shadow-[0px_2px_5px_0px_rgba(0,0,0,0.10)]",
            "flight_title": "airlineTruncate",
            "flight_price": "h6 text-primary font-bold",
            "flight_duration": "body-sm text-secondary",
            "flight_departure": "h6 text-primary font-medium",
        },
        "Trip": {
            "flight_listing": "f-info-head",
            "flight_title": "flights-name",
            "flight_price": "ThemeColor8 f-20 o-price-flight_b825 no-cursor_1b76",
            "flight_duration": [
                "flightinfoduration",
                "flight-info-duration_576d",
            ],
            "flight_departure": "flight-info-airline__timers_39aa",
            "flight_image": "flight-info-airline__logo airline-logo"
        },
        "Cleartrip": {
            "flight_listing": "ba bc-neutral-100 br-12 p-4 tp-box-shadow td-200 p-relative intl-tuple ow-tuple-container--intl pt-1 hover:elevation-3",
            "flight_title": "fs-4 fw-500 c-white",
            "flight_price": "m-0 fs-6 fw-600 c-neutral-900 ws-nowrap h-7",
            "flight_duration": "c-white fs-2 fw-500",
            "flight_departure": "fs-7 fw-500 c-white",
        },
    }

    all_data = []
    for site, url in urls.items():
        scraper = FlightScraper(url, site, selectors[site])
        df = scraper.extract_flight_details()
        all_data.append(df)

    final_df = pd.concat(all_data, ignore_index=True)
    final_df = final_df[final_df["Title"] != "N/A"]

    final_df["Departure"] = final_df["Departure"].apply(filter_departure_time)

    print(final_df)
    final_df.to_json("flights.json", orient="records", indent=4)
    i=2
    for _, row in final_df.iterrows():
        duration = row["Duration"]  # e.g., "3h 25m"
        hours = 0
        minutes = 0

        if 'h' in duration:
            hours = int(duration.split('h')[0].strip())
            duration = duration.split('h')[1]

        if 'm' in duration:
            minutes = int(duration.split('m')[0].strip())

        dur_num = hours * 60 + minutes

        departure_time = row["Departure"]  # e.g., "19:15"
        dept_num = int(departure_time.replace(":", ""))
        price_str = row["Price"]  # e.g., "Rs.3,608"
        price_num = int(price_str.replace("Rs.", "").replace(",", "").strip())  

        FlightDetails.objects.create(
            flight_title=row["Title"],
            flight_departure=row["Departure"],
            flight_arrival=row["Arrival"],
            flight_duration=row["Duration"],
            flight_price=row["Price"],
            flight_image_url=row["Image_URL"],
            flight_page_url=trip_url,
            site_name = "trip.com",
            fr_lc = f_id,
            to_lc = t_id,
            stop_type = "",
            free_meal = row["Free_Meal"],
            fl_sl_no = i,
            fl_durat_num = dur_num,
            fl_price_num = price_num,
            fl_dept_num = dept_num
        )
        i=i+2
        print(row["Title"])
        print(row["Departure"])
        print(row["Arrival"])
        print(row["Duration"])
        print(row["Price"])
        print(i)
        print(dur_num)
        print(price_num)
        print(dept_num)
        print("")

    return final_df


# Execute the scraper
