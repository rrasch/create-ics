#!/usr/bin/python3

# import mechanize

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import tomli

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

end_date = driver.find_element_by_xpath("//div[@id='endDate']/input")
end_date.click()
end_date.clear()
end_date.send_keys("12/15/2022")
end_date.send_keys(Keys.RETURN)

time.sleep(5)

start_date = driver.find_element_by_xpath("//div[@id='startDate']/input")
start_date.click()
start_date.clear()
start_date.send_keys("10/30/2022")
start_date.send_keys(Keys.RETURN)

time.sleep(5)

driver.find_element_by_id("membership-clubvisits-filters-go-btn").click()

time.sleep(10)

driver.find_element_by_id("pt-print").click()
