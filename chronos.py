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
from selenium.webdriver.chrome.options import Options  # Add this import at the top with other imports
import logging
import warnings
import os

# Add these at the top of your file, after the imports
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging
warnings.filterwarnings('ignore')  # Suppress general warnings
logging.getLogger('selenium').setLevel(logging.ERROR)  # Only show selenium errors
logging.getLogger('urllib3').setLevel(logging.ERROR)  # Suppress urllib3 logging
logging.basicConfig(level=logging.ERROR)  # Set basic config to only show errors

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
    """Initialize a headless Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # Add these new options
    chrome_options.add_argument('--log-level=3')  # Set Chrome logging level
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Disable logging
    chrome_options.add_argument('--silent')  # Run in silent mode
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(600, 600)
    return driver

def login(driver):
    # Load credentials from credentials.txt
    username = credentials.get("USERNAME")
    password = credentials.get("PASSWORD")
    
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

    # Replace the while loop print statements with a single initial message
    print("Check your phone for duo authentication...")
    while "duosecurity.com" in driver.current_url:
        try:
            # Automatically click the "Trust this browser" button for duo
            duo_button = driver.find_element(By.ID, "trust-browser-button")
            duo_button.click()
        except WebDriverException:
            pass
        time.sleep(2)
    
    print("Authentication completed")

rooms_booked = 0

def book_room(driver=None):
    global rooms_booked
    
    if driver is None:
        driver = initialize_driver()
        login(driver)
    
    try:
        importlib.reload(config)
        room_data = config.config
        
        start_time = room_data["start_time"]
        end_time = room_data["end_time"]
        
        while start_time < end_time and rooms_booked < 3:
            try:
                session_end = min(start_time + 7200, end_time)
                
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

                # Use explicit waits with timeouts
                wait = WebDriverWait(driver, 10)
                
                # Wait for and fill form fields
                name_field = wait.until(EC.presence_of_element_located((By.ID, "name")))
                name_field.send_keys(room_data["room_title"])
                
                description = wait.until(EC.presence_of_element_located((By.ID, "description")))
                description.send_keys(room_data["room_description"])
                
                room_type = wait.until(EC.presence_of_element_located((By.ID, "type")))
                Select(room_type).select_by_value("W")
                
                phone = wait.until(EC.presence_of_element_located((By.ID, "f_phone")))
                phone.send_keys(room_data["phone_number"])
                
                email = wait.until(EC.presence_of_element_located((By.ID, "f_email")))
                email.send_keys(room_data["email"])

                # Wait for conflict checks with timeout
                wait.until(lambda driver: driver.find_element(By.ID, "conflict_check").get_attribute("title") != "")
                wait.until(lambda driver: driver.find_element(By.ID, "policy_check").get_attribute("title") != "")
                
                conflict_title = driver.find_element(By.ID, "conflict_check").get_attribute("title")
                policy_title = driver.find_element(By.ID, "policy_check").get_attribute("title")

                if conflict_title != "No scheduling conflicts" or policy_title != "No policy conflicts":
                    print("Conflict detected! Skipping this session.")
                    print("Conflict:", conflict_title)
                    print("Policy:", policy_title)
                    
                    if "maximum" in policy_title or "3 weeks" in policy_title:
                        rooms_booked = 3
                        print("Booking limit reached.")
                        break
                else:
                    submit_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "default_action")))
                    submit_button.click()
                    print("Room booked successfully!")
                    rooms_booked += 1

                start_time = session_end

                if rooms_booked >= 3:
                    rooms_booked = 0
                    booked_url = (f"https://bookings.ok.ubc.ca/studyrooms/index.php?view=day"
                                f"&page_date={room_data['date']}"
                                f"&area={room_data['area']}")
                    driver.get(booked_url)
                    break
                    
            except Exception as e:
                print(f"Error during booking attempt: {str(e)}")
                start_time = session_end  # Move to next slot even if current fails
                continue
            
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
