#!/usr/bin/python3

from collections import defaultdict
from datetime import datetime, timedelta
from dateutil import tz
from dateutil.parser import parse
from icalendar import Calendar, Event
from pathlib import Path
from pprint import pprint
import argparse
import os
import pytz
import re


def change_ext(filename, new_ext):
    basename, ext = os.path.splitext(filename)
    return f"{basename}{new_ext}"


def is_dst(dt, timeZone):
    aware_dt = timeZone.localize(dt)
    return aware_dt.dst() != timedelta(0, 0)


def valid_year(s):
    try:
        return datetime.strptime(s, "%Y")
    except ValueError:
        msg = "not a valid year: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)


script_dir = os.path.dirname(os.path.realpath(__file__))
script_name = Path(__file__).stem
location_file = os.path.join(script_dir, "location.txt")

parser = argparse.ArgumentParser(
    description="Create calendar for fitness club checkins."
)
parser.add_argument(
    "checkins_file",
    metavar="CHECKIN_TXT_FILE",
    help="txt file containing checkin times",
)
parser.add_argument("year", metavar="YEAR", type=valid_year)
args = parser.parse_args()

year = args.year.strftime("%Y")

ics_file = change_ext(args.checkins_file, ".ics")
if os.path.isfile(ics_file):
    print(f"Calendar file {ics_file} already exists.")
    exit(0)

cal = Calendar()
cal.add("prodid", f"-//rrasch/GymCalendar//EN")
cal.add("version", "2.0")

with open(location_file) as fh:
    location = fh.readline().strip()
    # print(location)

with open(args.checkins_file) as fh:
    lines = fh.read().splitlines()

lines = list(filter(None, lines))

# pprint(lines)

line_iter = iter(lines)

local_timezone = pytz.timezone("America/New_York")

dates = defaultdict(list)

for line in line_iter:
    date_match = re.search(r"^(\d+/\d+)", line)
    if date_match:
        date = date_match.group(1)
        time = next(line_iter)
        time = re.sub(r"\s*=\s*", "", time)
        time = re.sub(r":/", ":7", time)
        time_match = re.search("^(\d+):(\d+)([ap]m)", time)
        if not time_match:
            raise ValueError(f"Invalid time {date} {time}")
        hour = time_match.group(1)
        minutes = int(time_match.group(2))
        ampm = time_match.group(3)
        full_date = f"{date}/{year} {hour}:{minutes:02d}{ampm}"
        print(full_date)

        dates[date].append(time)

        start_time = parse(full_date)
        # start_time = start_time.replace(tzinfo=tz.tzlocal())
        start_time = local_timezone.localize(start_time)
        end_time = start_time + timedelta(hours=2)

        # print(start_time.strftime('%Y-%m-%d %I:%M %p %Z%z'))
        # print(start_time.astimezone().strftime('%Y-%m-%d %I:%M %p %Z%z'))
        # print(end_time.astimezone().strftime('%Y-%m-%d %I:%M %p %Z%z'))

        uid = start_time.strftime("%Y%m%d%I%M%p%Z") + "@MyGymCalendar"

        event = Event()
        event.add("summary", "Gym Workout")
        event.add("description", f"Gym Workout {full_date}")
        event.add("dtstart", start_time)
        event.add("dtend", end_time)
        event.add("location", location)
        event["uid"] = uid
        cal.add_component(event)

print("Dates with multiple checkins:")
for date, times in dates.items():
    if len(times) > 1:
        print(f"{date}: {times}")

with open(ics_file, "wb") as fh:
    fh.write(cal.to_ical())
