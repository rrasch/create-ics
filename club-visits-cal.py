#!/usr/bin/env python3

from datetime import timedelta
from dateutil.parser import parse
from icalendar import Calendar, Event
import pandas as pd
import pytz
import re
import tabula

file = "Club-Visits-20211230-20221230.pdf"

local_timezone = pytz.timezone("US/Eastern")

pd.set_option(
    "display.max_columns", None,
    "display.max_rows", None,
    "display.width", 0
)

pdopt = {"header": None}

tables = tabula.read_pdf(file, pages="all", pandas_options=pdopt)

tables[0].drop(index=0, inplace=True)

cal = Calendar()
cal.add("prodid", f"-//rrasch/ClubCheckinCalendar//EN")
cal.add("version", "2.0")

for df in tables:
    for index, row in df.iterrows():
        checkin_time, club, address = row

        club = club.replace("\r", " ")
        club = re.sub(r" SS$", " Super Sport", club)

        start_time = parse(checkin_time)
        start_time = local_timezone.localize(start_time)
        end_time = start_time + timedelta(hours=2)

        uid = start_time.strftime("%Y%m%d%I%M%p%Z") + "@CheckinCalendar"

        event = Event()
        event.add("summary", "Gym Workout")
        event.add("description", f"Gym Workout {checkin_time}")
        event.add("dtstart", start_time)
        event.add("dtend", end_time)
        event.add("location", f"{club}, {address}")
        event["uid"] = uid
        cal.add_component(event)

with open("checkins.ics", "wb") as fh:
    fh.write(cal.to_ical())

