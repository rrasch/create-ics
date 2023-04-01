#!/usr/bin/env python3

from datetime import timedelta
from dateutil.parser import parse
from geopy.geocoders import GoogleV3
from icalendar import Calendar, Event
import argparse
import os
import pandas as pd
import pytz
import re
import tabula


def change_ext(filename, new_ext):
    basename, ext = os.path.splitext(filename)
    return f"{basename}{new_ext}"

parser = argparse.ArgumentParser(
    description="Create calendar for fitness club checkins.")
parser.add_argument("pdf_file", metavar="CHECKIN_PDF_FILE",
    help="pdf file containing checkin times")
args = parser.parse_args()

ics_file = change_ext(args.pdf_file, ".ics")
if os.path.isfile(ics_file):
    print(f"Calendar file {ics_file} already exists.")
    exit(0)

maps_api_key = os.environ.get("MAPS_API_KEY")
geolocator = GoogleV3(api_key=maps_api_key)

local_timezone = pytz.timezone("US/Eastern")

pd.set_option(
    "display.max_columns", None,
    "display.max_rows", None,
    "display.width", 0
)

pdopt = {"header": None}

tables = tabula.read_pdf(args.pdf_file, pages="all", pandas_options=pdopt)

tables[0].drop(index=0, inplace=True)

cal = Calendar()
cal.add("prodid", f"-//rrasch/ClubCheckinCalendar//EN")
cal.add("version", "2.0")

cleaned_address = {}

for df in tables:
    for index, row in df.iterrows():
        checkin_time, club, address = row

        club = club.replace("\r", " ")
        club = re.sub(r" SS$", " Super Sport", club)

        if address not in cleaned_address:
            cleaned_address[address] = geolocator.geocode(address)

        location = f"{club}, {cleaned_address[address]}"

        start_time = parse(checkin_time)
        start_time = local_timezone.localize(start_time)
        end_time = start_time + timedelta(hours=2)

        uid = start_time.strftime("%Y%m%d%I%M%p%Z") + "@CheckinCalendar"

        event = Event()
        event.add("summary", "Gym Workout")
        event.add("description", f"Gym Workout {checkin_time}")
        event.add("dtstart", start_time)
        event.add("dtend", end_time)
        event.add("location", location)
        event["uid"] = uid
        cal.add_component(event)

with open(ics_file, "wb") as fh:
    fh.write(cal.to_ical())

