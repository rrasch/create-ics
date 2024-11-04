#!/usr/bin/python3

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import tz
from dateutil.parser import parse
from geopy.geocoders import GoogleV3
from icalendar import Calendar, Event, vCalAddress, vText
from pathlib import Path
from pprint import pprint
from urllib.parse import urlparse, parse_qs
import argparse
import logging
import os
import pytz
import re
import tzlocal


def main():
    parser = argparse.ArgumentParser(
        description="Download club visits pdf report.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("html_file", help="Input schedule html file")
    parser.add_argument("ics_file", nargs="?", help="Output calendar ics file")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debugging"
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)

    api_key = os.environ["MAPS_API_KEY"]

    geolocator = GoogleV3(api_key=api_key)

    script_name = Path(__file__).stem

    soup = BeautifulSoup(open(args.html_file), "html.parser")

    team_name = soup.find("meta", {"property": "og:site_name"})["content"]
    logging.debug(f"{team_name=}")

    address_lines = (
        soup.find(
            "span",
            class_="site-nav-address--title",
            string="Middle & Upper School",
        )
        .find_next_sibling("p")
        .get_text()
        .split("\n")[1:]
    )
    address = ", ".join([line.strip() for line in address_lines])

    logging.debug(f"{address=}")

    team_address = geolocator.geocode(address).address
    logging.debug(f"{team_address=}")

    schedule_table = soup.find(
        "table", class_=re.compile("athletics-event-table")
    ).tbody

    cal = Calendar()

    # Some properties are required to be compliant
    cal.add("prodid", f"-//{script_name}//{team_name}//EN")
    cal.add("version", "2.0")

    local_timezone = pytz.timezone(tzlocal.get_localzone_name())
    today = datetime.now()
    this_year = today.year
    next_year = this_year + 1

    for tr in schedule_table.find_all("tr"):
        tds = tr.find_all("td")
        day, date, time, location, game_type, opponent = [
            td.get_text().strip() for td in tds
        ]

        address = None
        map_link = tds[3].find("a")
        if map_link:
            address = parse_qs(urlparse(map_link["href"]).query)["q"][0]

        logging.debug(f"----------")
        logging.debug(f"{day=}")
        logging.debug(f"{date=}")
        logging.debug(f"{time=}")
        logging.debug(f"{location=}")
        logging.debug(f"{game_type=}")
        logging.debug(f"{opponent=}")
        logging.debug(f"{address=}")

        if not (
            game_type in ["Game", "Scrimmage"] or "game day" in day.lower()
        ):
            continue

        if "Zambetti" in location:
            title = f"{opponent} vs. {team_name}"
            ev_location = team_address
        else:
            title = f"{team_name} vs. {opponent}"
            if address:
                ev_location = geolocator.geocode(address).address
            else:
                ev_location = location

        title += f" High School Basketball {game_type.title()}"

        logging.debug(f"{title=}")
        logging.debug(f"{ev_location=}")

        start_time = parse(f"{date}, {this_year} {time}")
        if start_time < today:
            start_time = parse(f"{date}, {next_year} {time}")
        start_time = local_timezone.localize(start_time)
        end_time = start_time + timedelta(hours=1, minutes=30)

        logging.debug(start_time.strftime("%Y-%m-%d %I:%M %p"))
        logging.debug(start_time.astimezone().strftime("%Y-%m-%d %I:%M %p"))
        logging.debug(end_time.astimezone().strftime("%Y-%m-%d %I:%M %p"))

        uid = (
            start_time.strftime("%Y%m%d%I%M%p%Z")
            + "@"
            + team_name.replace(" ", "")
        )

        event = Event()
        event.add("summary", title)
        event.add("description", title)
        event.add("dtstart", start_time)
        event.add("dtend", end_time)
        event.add("location", ev_location)
        event["uid"] = uid
        cal.add_component(event)

    logging.info(f"Calendar has {len(cal.subcomponents)} events.")

    if args.ics_file:
        with open(args.ics_file, "wb") as fh:
            fh.write(cal.to_ical())
    else:
        print(cal.to_ical().decode(), end="")


if __name__ == "__main__":
    main()
