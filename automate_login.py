from selenium import webdriver
import time
from datetime import datetime, timedelta
from selenium.webdriver.chrome.service import Service


def open_browser():
    service = Service(executable_path='msedgedriver.exe')
    driver = webdriver.Edge(service=service)
    driver.get("https://imh.99b1b438eb1b4006.pw/kefu/pc_list")


def close_browser(driver):
    driver.quit()


def refresh_page(driver):
    driver.refresh()


scheduled_times = {
    'Monday' : ['15:00', '21:00'],
    'Tuesday' : ['18:00', '03:00'],
    'Wednesday' : ['15:00', '21:00'],
    'Thursday' : ['15:00', '21:00'],
    'Friday' : ['15:00', '21:00'],
    'Saturday' : ['09:00', '16:00'],
    'Sunday' : ['15:00', '21:00']
}

refresh_interval = 120  # in seconds (2 minutes)
driver = None  # Initialize the driver variable outside the loop

while True:
    current_time = datetime.now().strftime("%H:%M")
    current_day = datetime.now().strftime("%A")

    open_time, close_time = scheduled_times[current_day][0], scheduled_times[current_day][1]

    if current_time == open_time:
        driver = open_browser()

    if driver and current_time == close_time:
        close_browser(driver)

        # Calculate the next day's close time for Tuesday
        if current_day == 'Tuesday':
            next_day_close_time = datetime.strptime(scheduled_times['Wednesday'][1], "%H:%M")
            next_day_close_time += timedelta(days=1)
            scheduled_times['Wednesday'][1] = next_day_close_time.strftime("%H:%M")

    if driver:  # Check if the driver is defined before calling refresh_page or closing the browser
        refresh_page(driver)

        time.sleep(refresh_interval)
