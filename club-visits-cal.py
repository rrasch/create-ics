#!/usr/bin/env python3

from datetime import datetime, timedelta
from dateutil.parser import parse
from geopy.geocoders import GoogleV3
from icalendar import Calendar, Event
import argparse
import logging
import os
import pandas as pd
import pytz
import re
import tabula
import warnings


def change_ext(filename, new_ext):
    basename, ext = os.path.splitext(filename)
    return f"{basename}{new_ext}"


def main():
    parser = argparse.ArgumentParser(
        description="Create calendar for fitness club checkins."
    )
    parser.add_argument(
        "pdf_file",
        metavar="CHECKIN_PDF_FILE",
        help="pdf file containing checkin times",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force removal of output file",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debugging"
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)

    ics_file = change_ext(args.pdf_file, ".ics")
    if not args.force and os.path.isfile(ics_file):
        print(f"Calendar file {ics_file} already exists.")
        exit(0)

    maps_api_key = os.environ["MAPS_API_KEY"]
    geolocator = GoogleV3(api_key=maps_api_key)

    local_timezone = pytz.timezone("America/New_York")

    pd.set_option(
        "display.max_columns",
        None,
        "display.max_rows",
        None,
        "display.width",
        0,
    )

    pdopt = {"header": None}

    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore", category=FutureWarning)
        tables = tabula.read_pdf(
            args.pdf_file, pages="all", lattice=True, pandas_options=pdopt
        )

    # remove row with column names
    tables[0].drop(index=0, inplace=True)

    cal = Calendar()
    cal.add("prodid", f"-//rrasch/ClubCheckinCalendar//EN")
    cal.add("version", "2.0")

    cleaned_address = {}
    checkins = {}
    prev_time = None
    # prev_time = datetime.min.replace(tzinfo=pytz.UTC)

    for df in reversed(tables):
        df.dropna(axis=1, how="all", inplace=True)

        for index, row in df[::-1].iterrows():
            logging.debug("row:\n%s", row)

            checkin_time, club, address = row
            logging.debug(f"{checkin_time=}")

            if checkin_time in checkins:
                print(f"Duplicate {checkin_time=}")
                continue

            checkins[checkin_time] = 1

            start_time = parse(checkin_time)
            start_time = local_timezone.localize(start_time)
            end_time = start_time + timedelta(hours=2)

            if prev_time is not None:
                time_diff = start_time - prev_time
                logging.debug(f"{time_diff=}")
                diff_hours = abs(time_diff.total_seconds()) / (60 * 60)
                if diff_hours < 2:
                    print(
                        f"Checkin time {checkin_time} is within 2 hours of"
                        f" {prev_time}"
                    )
                    continue

            prev_time = start_time

            club = club.replace("\r", " ")
            club = re.sub(r" SS$", " Super Sport", club)

            if address not in cleaned_address:
                cleaned_address[address] = geolocator.geocode(address)

            location = f"{club}, {cleaned_address[address]}"

            uid = start_time.strftime("%Y%m%d%I%M%p%Z") + "@CheckinCalendar"

            event = Event()
            event.add("summary", "Gym Workout")
            event.add("description", f"Gym Workout {checkin_time}")
            event.add("dtstart", start_time)
            event.add("dtend", end_time)
            event.add("location", location)
            event["uid"] = uid
            cal.add_component(event)

    logging.debug(cal.to_ical().decode("utf-8").replace("\r\n", "\n").strip())

    print(f"Calendar has {len(cal.subcomponents)} checkins.")

    with open(ics_file, "wb") as fh:
        fh.write(cal.to_ical())


if __name__ == "__main__":
    main()
