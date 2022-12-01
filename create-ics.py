#!/usr/bin/python3

from bs4 import BeautifulSoup
from datetime import timedelta
from dateutil import tz
from dateutil.parser import parse
from geopy.geocoders import GoogleV3
from icalendar import Calendar, Event, vCalAddress, vText
from pathlib import Path
from pprint import pprint
import os
import re


api_key = os.environ.get("MAPS_API_KEY")

geolocator = GoogleV3(api_key=api_key)

script_name = Path(__file__).stem

filename = "schedule.html"

soup = BeautifulSoup(open(filename), "html.parser")

team_name = (
    soup.find("h1", {"id": "Team_highlight_info1_Header"}).get_text().split()[0]
)

team_address = geolocator.geocode(
    soup.find("address").get_text().strip()
).address

schedule_table = soup.find("table", {"id": "schedule"}).tbody

cal = Calendar()

# Some properties are required to be compliant
cal.add("prodid", f"-//{script_name}//{team_name}//EN")
cal.add("version", "2.0")

for tr in schedule_table.find_all("tr"):
    date = tr.find(class_="event-time")["title"]
    opponent = (
        tr.find(class_=re.compile(r"contest-type-indicator"))
        .contents[0]
        .strip()
    )
    opponent_city = tr.find(class_="contest-city-state").get_text().strip("()")
    away = tr.find(class_="away-indicator")
    location = tr.find(class_="contest-location")["title"]

    # print(date)
    # print(opponent)
    # print(away)
    # print(opponent_city)
    # print(location)

    if away:
        title = f"{team_name} vs. {opponent}"
        address = geolocator.geocode(f"{location}, {opponent_city}")
        # pprint(address.raw)
    else:
        title = f"{opponent} vs. {team_name}"
        address = team_address

    title += " HS Basketball Game"

    # print(date)
    # print(opponent)
    # print(opponent_city)
    # print(title)

    start_time = parse(date).replace(tzinfo=tz.tzutc())
    start_time = start_time - timedelta(hours=3)
    end_time = start_time + timedelta(hours=2)

    # print(start_time.strftime('%Y-%m-%d %I:%M %p'))
    # print(start_time.astimezone().strftime('%Y-%m-%d %I:%M %p'))
    # print(end_time.astimezone().strftime('%Y-%m-%d %I:%M %p'))

    uid = re.sub(r"[-:]", "", date) + "@" + team_name

    event = Event()
    event.add("summary", title)
    event.add("description", title)
    event.add("dtstart", start_time)
    event.add("dtend", end_time)
    event.add("location", f"{location}, {address}")
    event["uid"] = uid
    cal.add_component(event)

with open("out.ics", "wb") as fh:
    fh.write(cal.to_ical())
