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

driver.set_window_size(600, 600)
driver.get(base_booking_url)

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

rooms_booked = 0

def book_room():
    global rooms_booked
    
    # Reload the config file to get the latest data
    importlib.reload(config)
    room_data = config.config
    
    start_time = room_data["start_time"]
    end_time = room_data["end_time"]
    
    # Process the bookings in 2-hour chunks
    while start_time < end_time and rooms_booked < 3:
        # Ensure max session is 2 hours (7200 seconds)
        session_end = min(start_time + 7200, end_time)
        
        # Construct the booking URL
        url = (
            f"https://bookings.ok.ubc.ca/studyrooms/edit_entry.php?drag=1"
            f"&area={room_data['area']}"
            f"&start_seconds={start_time}"
            f"&end_seconds={session_end}"
            f"&rooms[]={room_data['room']}"
            f"&start_date={room_data['date']}"
            f"&top=0"
        )
        
        print(f"Booking room from {start_time} to {session_end}: {url}")
        driver.get(url)

        # Input details
        driver.find_element(By.ID, "name").send_keys(room_data["room_title"])
        driver.find_element(By.ID, "description").send_keys(room_data["room_description"])
        Select(driver.find_element(By.ID, "type")).select_by_value("W")
        driver.find_element(By.ID, "f_phone").send_keys(room_data["phone_number"])
        driver.find_element(By.ID, "f_email").send_keys(room_data["email"])

        # Check for conflicts
        while driver.find_element(By.ID, "conflict_check").get_attribute("title") == "" or \
              driver.find_element(By.ID, "policy_check").get_attribute("title") == "":
            print("Checking for conflicts...")
            time.sleep(1)
        
        conflict_title = driver.find_element(By.ID, "conflict_check").get_attribute("title")
        policy_title = driver.find_element(By.ID, "policy_check").get_attribute("title")

        if conflict_title != "No scheduling conflicts" or policy_title != "No policy conflicts":
            print("Conflict detected! Skipping this session.")
            print("Conflict:", conflict_title)
            print("Policy:", policy_title)
            # goto the booking url to view the conflict 
            # it looks like this
            # https://bookings.ok.ubc.ca/studyrooms/index.php?view=day&page_date=2025-03-21&area=6
            conflict_url = (f"https://bookings.ok.ubc.ca/studyrooms/index.php?view=day"
                            f"&page_date={room_data['date']}"
                            f"&area={room_data['area']}")
            driver.get(conflict_url)
            
            # Move to the next session
        else:
            print("No conflicts, booking room...")
            driver.find_element(By.CLASS_NAME, "default_action").click()
            rooms_booked += 1
        
        # Move to the next session
        start_time = session_end

        if rooms_booked >= 3:
            print("Reached booking limit.")
            rooms_booked = 0
            break


# Dev mode
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
