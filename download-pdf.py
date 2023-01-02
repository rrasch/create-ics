#!/usr/bin/python3


from dateparser import parse
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import argparse
import time
import tomli


def format_date(date):
    return date.strftime("%m/%d/%Y")

def first_day_of_prev_month():
    now = date.today()
    first_day = (now - timedelta(days=now.day)).replace(day=1)
    return format_date(first_day)

def last_day_of_prev_month():
    last_day = date.today().replace(day=1) - timedelta(days=1)
    return format_date(last_day)


parser = argparse.ArgumentParser(
    description="Download club visits pdf report.",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--start-date", "-s",
    default=first_day_of_prev_month(),
    help="Start date of report period")
parser.add_argument("--end-date", "-e",
    default=last_day_of_prev_month(),
    help="End date of report period")
args = parser.parse_args()


start_date_str = format_date(parse(args.start_date))
end_date_str = format_date(parse(args.end_date))

print(f"start date: {start_date_str}")
print(f"end date:   {end_date_str}")

with open("config.toml", "rb") as f:
    config = tomli.load(f)

driver = webdriver.Chrome()

driver.maximize_window()

driver.get(config["visits_url"])

driver.refresh()

driver.find_element_by_id("myaccount-login-info-usrname").send_keys(config["username"])
driver.find_element_by_id("myaccount-login-info-passwrd").send_keys(config["password"])
driver.find_element_by_id("myaccount-login-info-passwrd").submit()

time.sleep(10)

end_date_input = driver.find_element_by_xpath("//div[@id='endDate']/input")
end_date_input.click()
end_date_input.clear()
end_date_input.send_keys(end_date_str)
end_date_input.send_keys(Keys.RETURN)

time.sleep(5)

start_date_input = driver.find_element_by_xpath("//div[@id='startDate']/input")
start_date_input.click()
start_date_input.clear()
start_date_input.send_keys(start_date_str)
start_date_input.send_keys(Keys.RETURN)

time.sleep(5)

driver.find_element_by_id("membership-clubvisits-filters-go-btn").click()

time.sleep(10)

driver.find_element_by_id("pt-print").click()