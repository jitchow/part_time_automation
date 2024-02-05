from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

import time
from datetime import datetime

scheduled_times = {
    'Monday': ['15:00', '21:00'],
    'Tuesday': ['18:00', '11:59'],
    'Wednesday': ['15:00', '21:00'],
    'Thursday': ['15:00', '21:00'],
    'Friday': ['15:00', '21:00'],
    'Saturday': ['09:00', '16:00'],
    'Sunday': ['15:00', '21:00']
}


def is_time_between(start_time, end_time, check_time=None):
    check_time = check_time or datetime.now().strftime('%H:%M')
    start_time = datetime.strptime(start_time, '%H:%M')
    end_time = datetime.strptime(end_time, '%H:%M')
    check_time = datetime.strptime(check_time, '%H:%M')
    return start_time <= check_time <= end_time


def open_browser_at_scheduled_time():
    while True:
        current_time = datetime.now().strftime('%H:%M')
        current_day = datetime.now().strftime('%A')  # Get the current day of the week

        if current_day in scheduled_times:
            open_time, close_time = scheduled_times[current_day]

            if is_time_between(open_time, close_time, current_time):
                # Open the browser and navigate to the specified URL
                service = Service(executable_path='msedgedriver.exe')
                driver = webdriver.Edge(service=service)
                driver.get("https://imh.99b1b438eb1b4006.pw/kefu/pc_list")

                # Fill in the username and password fields
                username_input = driver.find_element(By.CLASS_NAME, 'ivu-input-large')
                password_input = driver.find_element(By.XPATH, '//input[@type="password"]')

                username_input.send_keys('xiaoyu')
                password_input.send_keys('qweqwe')

                # Click the login button
                login_button = driver.find_element(By.XPATH, '//button[contains(@class, "ivu-btn-primary")]')
                login_button.click()

                # Refresh the page every 2 minutes
                while is_time_between(open_time, close_time):
                    time.sleep(5)

                    # Accept any alert or confirmation popup
                    try:
                        driver.switch_to.alert.accept()
                    except:
                        pass

                    driver.refresh()

                # Close the browser when it's time to close
                driver.quit()
            else:
                # Sleep for a while before checking the time again
                time.sleep(60)
        else:
            print(f'No scheduled times for {current_day}. Waiting for the next day...')
            # Sleep for a while before checking the time again
            time.sleep(60)


# Run the function
open_browser_at_scheduled_time()
