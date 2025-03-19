import requests
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select 
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
from dotenv import load_dotenv

# load config
import importlib
import config

# Load environment variables from .env file
load_dotenv()

# Load environment variables
username = os.getenv("UBC_USERNAME")
password = os.getenv("UBC_PASSWORD")

print("Username: ", username)
print("Password: ", password)

# Base URL for booking study rooms
base_booking_url = "https://bookings.ok.ubc.ca/studyrooms/"

# Start the Chrome browser
driver = webdriver.Chrome()

# Open the booking URL, and set the window size to 600x600
driver.get(base_booking_url)
driver.set_window_size(600, 600)

# Find the login button from the study room website and click it
driver.find_element(By.XPATH, "//input[@value='Log in']").click()

# wait for user to leave base_url
while driver.current_url == base_booking_url:
    print("Waiting for user to leave: ", driver.current_url)
    time.sleep(1)


# Find and fill in the username and password fields
driver.find_element(By.ID, "username").send_keys(username)
driver.find_element(By.ID, "password").send_keys(password)


# Click the login button on the CWL page
driver.find_element(By.XPATH, "//button[@type='submit']").click()

# now wait for user to leave "authentication.ubc.ca"
while "authentication.ubc.ca" in driver.current_url:
    print("Waiting for user to leave: authentication.ubc.ca")
    time.sleep(1)

# Wait for user to leave url that contains "duosecurity.com"
while "duosecurity.com" in driver.current_url:
    print("Please check your phone for Duo authentication")
    try:
        # Automatically click the "Trust this browser" button for duo
        duo_button = driver.find_element(By.ID, "trust-browser-button")
        duo_button.click()
    except WebDriverException:
        print()
        pass
    time.sleep(2)


# Now we are logged in and ready to book a room
# A room booking format looks like this:
# https://bookings.ok.ubc.ca/studyrooms/edit_entry.php?drag=1&area=6&start_seconds=23400&end_seconds=30600&rooms=28&start_date=2025-03-19&top=0
# min time, 6:00am, is 21600 seconds, max time, 12:30am which is
# you can book at max 2 hours, which is 7200 seconds
# date format is YYYY-MM-DD
# area is the building
# rooms[] is the room number


def book_room():
    importlib.reload(config)
    room_data = config.config
    # Before we construct the URL, we need to split the sessions into 2 hours intervals, max of 3 sessions
    
    # Construct the URL
    url = f"https://bookings.ok.ubc.ca/studyrooms/edit_entry.php?drag=1&area={room_data["area"]}&start_seconds={room_data["start_time"]}&end_seconds={config["end_time"]}&rooms[]={room_data["room"]}&start_date={room_data["date"]}&top=0"
    print("Booking room: ", url)
    
    # Open the URL
    driver.get(url)
    
    # input the room title
    driver.find_element(By.ID, "name").send_keys(room_data["room_title"])
    
    # input description
    driver.find_element(By.ID, "description").send_keys(room_data["room_description"])
    
    # select the room type
    # select the Instructional / Workshop option to differentiate from other bookings
    Select(driver.find_element(By.ID, "type")).select_by_value("W")
    
    # input phone number
    driver.find_element(By.ID, "f_phone").send_keys(room_data["phone_number"])
    
    # input email
    driver.find_element(By.ID, "f_email").send_keys(room_data["email"])
    
    # delay to allow the page to load the conflict checks
    
    # now check and see if there was any schedule conflicts,
    conflict_check = driver.find_element(By.ID, "conflict_check")
    
    # now check and see if there was any policy conflicts,
    policy_check = driver.find_element(By.ID, "policy_check")
    
    
    # if there are no schedule it will say "No schedule conflicts"
    # if there are no policy conflicts it will say "No policy conflicts"
    # so, we will wait until the title is not empty
    while conflict_check.get_attribute("title") == "" or policy_check.get_attribute("title") == "":
        print("Checking for conflicts...")
        time.sleep(1)

    # if there is conflicts, we will not book the room, back off to url
    if conflict_check.get_attribute("title") != "No schedule conflicts" or policy_check.get_attribute("title") != "No policy conflicts":
        print("There are conflicts, I cannot book this room... backing off to main page")
        # print the conflict and policy checks
        print("Conflict: ", conflict_check.get_attribute("title"))
        print("Policy: ", policy_check.get_attribute("title"))
        driver.get(base_booking_url)
        return
    
    # print the conflict and policy checks
    print(conflict_check.get_attribute("title"))
    print(policy_check.get_attribute("title"))
    
    # find the save button and click it
    # driver.find_element(By.CLASS_NAME, "default_action").click()


while True:
    command = input("Enter Selenium command (or 'exit'): ")
    if command.lower() == "exit":
        break
    try:
        exec(command)
    except Exception as e:
        print(f"Error: {e}")


# Wait 
time.sleep(60)

# exit the browser
driver.quit()
exit()
