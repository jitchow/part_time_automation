from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert 

import time
from datetime import datetime
import json
import os
from dotenv import load_dotenv
load_dotenv()
from config import scheduled_times_login, telegram_bot

# Use your own values from my.telegram.org
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_TEST_CHANNEL_ID = int(os.getenv('TELEGRAM_TEST_CHANNEL_ID'))
CUST_LIST_JSON = os.getenv('CUST_LIST_JSON')


def is_time_between(start_time, end_time, check_time=None):
    check_time = check_time or datetime.now().strftime('%H:%M')
    start_time = datetime.strptime(start_time, '%H:%M')
    end_time = datetime.strptime(end_time, '%H:%M')
    check_time = datetime.strptime(check_time, '%H:%M')
    return start_time <= check_time <= end_time


def is_list_same(list1, list2):
    return len(list1) == len(list2) and all(x == y for x, y in zip(list1, list2))


def is_last_chat_item_right_box(driver):
    main_div = driver.find_element(By.ID, "chat_scroll")
    chat_items = main_div.find_elements(By.CSS_SELECTOR, "div.chat-item.right-box")

    # Check if the last direct child of main_div has class 'chat-item right-box'
    last_child = main_div.find_elements(By.XPATH, "./*")[-1]
    if last_child in chat_items:
        return True
    else:
        return False


def have_new_message(driver):
    if os.path.exists(CUST_LIST_JSON):
        with open(CUST_LIST_JSON, 'r') as file:
            old_names = json.load(file)
    else:
        old_names = []

    # Find all the <span> elements with class "name line1"
    name_elements = driver.find_elements(By.CSS_SELECTOR, "span.name.line1")
    new_names = [name_element.text for name_element in name_elements][:10]

    with open(CUST_LIST_JSON, 'w') as file:
        json.dump(new_names, file)

    # Compare if arrangement of both lists is same
    isListSame = is_list_same(new_names, old_names)
    isLastChatKefu = is_last_chat_item_right_box(driver)

    if not isListSame or not isLastChatKefu:
        return True
    return False


def telegram_send_notification(type):
    current_time = datetime.now().strftime('%H:%M:%S')
    messages = {
        'notification' : f"{current_time}: ⚠️  YOU HAVE NEW CUSTOMER ! ! ! ⚠️", 
        'online' : '客服 IS NOW ONLINE', 
        'offline' : '客服 IS NOW OFFLINE',
        'crashed' : 'Login crashed, running again.....'
    }
    caption = messages[type]

    try:
        telegram_bot.send_message(TELEGRAM_TEST_CHANNEL_ID, caption)
    except Exception as e:
        print(e)

    print('Sent: ' + caption)


def main():
    while True:
        current_time = datetime.now().strftime('%H:%M')
        current_day = datetime.now().strftime('%A')  # Get the current day of the week

        if current_day in scheduled_times_login:
            if current_day == 'Wednesday' and current_time < '04:00':
                open_time, close_time = ['00:00', '03:00']
            else:
                open_time, close_time = scheduled_times_login[current_day]
            
            if is_time_between(open_time, close_time, current_time):
                # Open the browser and navigate to the specified URL
                service = Service(executable_path=os.getenv('EDGE_DRIVER_PATH'))
                driver = webdriver.Edge(service=service)
                driver.get(os.getenv('LINK_LOGIN'))

                # Fill in the username and password fields
                username_input = driver.find_element(By.CLASS_NAME, 'ivu-input-large')
                password_input = driver.find_element(By.XPATH, '//input[@type="password"]')

                username_input.send_keys(os.getenv('USERNAME_KEFU'))
                password_input.send_keys(os.getenv('PASSWORD_KEFU'))

                # Click the login button
                driver.find_element(By.XPATH, '//button[contains(@class, "ivu-btn-primary")]').click()
                time.sleep(1)

                driver.maximize_window()

                telegram_send_notification('online')

                # Refresh the page every 2 minutes
                while is_time_between(open_time, close_time):
                    try: 
                        WebDriverWait(driver, 10).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                        driver.execute_script("window.location.reload(true);") 
                        print('R e f r e s h e d  !')
                    except Exception as e:
                        print(e)
                        driver.quit()
                        raise Exception
                    
                    try:  
                        # Accept any alert or confirmation popup
                        Alert(driver).accept()
                    except:
                        pass
                    
                    time.sleep(3)
                    haveNewMessage = have_new_message(driver)
                    if haveNewMessage:
                        telegram_send_notification('notification')

                    time.sleep(120)

                # Close the browser when it's time to close
                driver.find_element(By.XPATH, "//div[@class='status-box']").click()
                driver.find_element(By.XPATH, "//div[@class='online-down']//div[@class='item'][text()='离线']").click()
                time.sleep(2)

                driver.quit()
                telegram_send_notification('offline')
            else:
                # Sleep for a while before checking the time again
                time.sleep(60)
        else:
            print(f'No scheduled times for {current_day}. Waiting for the next day...')
            # Sleep for a while before checking the time again
            time.sleep(60)

while True:
    try:
        if __name__ == "__main__":
            main()
    except KeyboardInterrupt:
        break
    except:
        telegram_send_notification('crashed')
        print('Login crashed, running again.....')
