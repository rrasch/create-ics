#!/usr/bin/python3

from bs4 import BeautifulSoup
from datetime import date, timedelta
from geopy.geocoders import GoogleV3
from icalendar import Calendar, Event
from pathlib import Path
from pprint import pprint
from urllib import parse
import dateutil.parser
import os
import pytz
import re


api_key = os.environ.get("MAPS_API_KEY")

geolocator = GoogleV3(api_key=api_key)

script_name = Path(__file__).stem

filename = "index-tidy.html"

soup = BeautifulSoup(open(filename), "html.parser")

schedule_table = soup.find("tbody")

cal = Calendar()

team_name = soup.find("meta",
    {"property": "og:site_name"})["content"].split()[0]

# Some properties are required to be compliant
cal.add("prodid", f"-//{script_name}//{team_name}//EN")
cal.add("version", "2.0")

cols = {
    0: "day",
    1: "date",
    2: "time",
    3: "location",
    4: "type",
    5: "opponent",
}

local_timezone = pytz.timezone("US/Eastern")

today = date.today()

for tr in schedule_table.find_all("tr", recursive=False):
    td = tr.find_all("td", recursvie=False)

    fields = {}
    for idx, col_name in cols.items():
        fields[col_name] = td[idx].get_text().strip()

    if fields["type"] != "Game":
        continue

    home = fields["location"].startswith("Marc A. Zambetti")

    location = fields["location"]

    if home:
        title = f"{fields['opponent']} vs. {team_name}"
    else:
        title = f"{team_name} vs. {fields['opponent']}"
        maps_link = td[3].find("a", href=True, text=fields["location"])
        if maps_link:
            query = parse.parse_qs(parse.urlsplit(maps_link["href"]).query)
            location = geolocator.geocode(query["q"][0])

    title += " Boys Varsity Basketball Game"

    date = f"{fields['date']}, {today.year} {fields['time']}"

    start_time = dateutil.parser.parse(date)
    start_time = local_timezone.localize(start_time)
    end_time = start_time + timedelta(hours=2)

    uid = start_time.strftime("%Y%m%d%H%M") + "@" + team_name

    event = Event()
    event.add("summary", title)
    event.add("description", title)
    event.add("dtstart", start_time)
    event.add("dtend", end_time)
    event.add("location", location)
    event["uid"] = uid
    cal.add_component(event)

with open("varsity-schedule.ics", "wb") as fh:
    fh.write(cal.to_ical())

