import os
import django
import pandas as pd

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flightmatch.settings")
django.setup()

# Import the model
from backend.models import Airports  # Ensure this path is correct

# Load the Excel file
file_path = "D:/PROGRAMMING/PROJECTS/flightmatch/static/dataset/airports-code@public.xlsx"
df = pd.read_excel(file_path, engine="openpyxl")

# Required columns
columns = ["Airport Code", "Airport Name", "City Name", "Country Name", "Country Code"]

# Optional: Check if columns exist
if not all(col in df.columns for col in columns):
    raise ValueError("Excel file is missing one or more required columns.")

# Step 1: Delete all existing entries
Airports.objects.all().delete()
print("Old entries deleted from Airports table.")

# Step 2: Insert new data
for _, row in df.iterrows():
    Airports.objects.create(
        airport_code=row["Airport Code"],
        airport_name=row["Airport Name"],
        airport_city=row["City Name"],
        airport_country=row["Country Name"],
        airport_country_code=row["Country Code"],
        airport_search_element=f'{row["City Name"]} - {row["Airport Code"]} - {row["Country Name"]}'
    )

print("Data successfully imported into Airports table!")
