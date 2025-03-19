import requests
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select 
from selenium.common.exceptions import WebDriverException, NoSuchWindowException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import importlib
import config

def read_credentials():
    """Read credentials from credentials.txt"""
    creds = {}
    try:
        with open('credentials.txt', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    creds[key] = value
    except Exception as e:
        print(f"Error reading credentials: {e}")
    return creds

credentials = read_credentials()

def initialize_driver():
    driver = webdriver.Chrome()
    driver.set_window_size(600, 600)
    return driver

def login(driver):
    # Load credentials from credentials.txt
    username = credentials.get("UBC_USERNAME")
    password = credentials.get("UBC_PASSWORD")
    
    if not username or not password:
        raise Exception("Credentials not found in credentials.txt")
        
    # Base URL for booking study rooms
    base_booking_url = "https://bookings.ok.ubc.ca/studyrooms/"
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

rooms_booked = 0

def book_room(driver=None):
    global rooms_booked
    
    if driver is None:
        driver = initialize_driver()
        login(driver)
    
    try:
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
            
            print(f"\nBooking room from {convert_seconds_to_time(start_time)}"
                    f" - {convert_seconds_to_time(session_end)}")
            driver.get(url)

            # Add explicit waits
            wait = WebDriverWait(driver, 10)
            name_field = wait.until(EC.presence_of_element_located((By.ID, "name")))
            name_field.send_keys(room_data["room_title"])
            
            driver.find_element(By.ID, "description").send_keys(room_data["room_description"])
            Select(driver.find_element(By.ID, "type")).select_by_value("W")
            driver.find_element(By.ID, "f_phone").send_keys(room_data["phone_number"])
            driver.find_element(By.ID, "f_email").send_keys(room_data["email"])

            # Check for conflicts
            while driver.find_element(By.ID, "conflict_check").get_attribute("title") == "" or \
                  driver.find_element(By.ID, "policy_check").get_attribute("title") == "":
                time.sleep(1)
            
            conflict_title = driver.find_element(By.ID, "conflict_check").get_attribute("title")
            policy_title = driver.find_element(By.ID, "policy_check").get_attribute("title")

            if conflict_title != "No scheduling conflicts" or policy_title != "No policy conflicts":
                print("Conflict detected! Skipping this session.")
                print("Conflict:", conflict_title)
                print("Policy:", policy_title)
                
                # if the policy contains "maximum", then we have reached the booking limit
                if "maximum" in policy_title:
                    rooms_booked = 3
                    print(f"Sorry, you have reached booking limit of 3 per area per user.")
                if "3 weeks" in policy_title:
                    rooms_booked = 3
                    print("You have reached the booking limit of 3 weeks in advance.")
                # Move to the next session
            else:
                driver.find_element(By.CLASS_NAME, "default_action").click()
                print("Room booked successfully!")
                rooms_booked += 1
            
            # Move to the next session
            start_time = session_end

            if rooms_booked >= 3:
                rooms_booked = 0
                # goto the booking url to view the bookings
                # it looks like this
                # https://bookings.ok.ubc.ca/studyrooms/index.php?view=day&page_date=2025-03-21&area=6
                booked_url = (f"https://bookings.ok.ubc.ca/studyrooms/index.php?view=day"
                                f"&page_date={room_data['date']}"
                                f"&area={room_data['area']}")
                driver.get(booked_url)
                break
            
        return True
    
    except Exception as e:
        print(f"Booking error: {str(e)}")
        return False
        
def convert_seconds_to_time(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))

# Move dev mode code into main block
if __name__ == "__main__":
    # Dev mode
    driver = initialize_driver()
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
