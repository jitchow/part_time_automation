from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telethon import TelegramClient

import time
from datetime import datetime
import json
import asyncio

# Use your own values from my.telegram.org
api_id = 24923597
api_hash = "7a04f08385f68ff36841b0c65b83be86"
CHANNEL_ID = -4038638534  # -4041523708 kefu -4038638534 test
client = TelegramClient('session', api_id, api_hash)

scheduled_times = {
    'Monday': ['15:00', '21:00'],
    'Tuesday': ['18:00', '23:58'],
    'Wednesday': ['15:00', '21:00'],
    'Thursday': ['15:00', '21:00'],
    'Friday': ['15:00', '21:00'],
    'Saturday': ['09:00', '18:00'],
    # 'Sunday': ['15:00', '21:00']
}


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
    with open('cust_names.json', 'r') as file:
        old_names = json.load(file)

    # Find all the <span> elements with class "name line1"
    name_elements = driver.find_elements(By.CSS_SELECTOR, "span.name.line1")
    new_names = [name_element.text for name_element in name_elements][:10]

    with open('cust_names.json', 'w') as file:
        json.dump(new_names, file)

    # Compare if arrangement of both lists is same
    isListSame = is_list_same(new_names, old_names)
    isLastChatKefu = is_last_chat_item_right_box(driver)

    if not isListSame or not isLastChatKefu:
        return True
    return False


async def telegram_send_notification():
    current_time = datetime.now().strftime('%H:%M')
    try:
        caption = f"{current_time} : YOU HAVE NEW CUSTOMER ! ! ! ! !"
        async with client:
            await client.send_message(CHANNEL_ID, caption)
    except Exception as e:
        print(e)

    print('Sent: ' + caption)


async def main():
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
                driver.find_element(By.XPATH, '//button[contains(@class, "ivu-btn-primary")]').click()
                time.sleep(1)

                # Minimize the browser window
                driver.maximize_window()

                # Refresh the page every 2 minutes
                while is_time_between(open_time, close_time):
                    driver.refresh()

                    # Accept any alert or confirmation popup
                    try:
                        driver.switch_to.alert.accept()
                    except:
                        pass

                    haveNewMessage = have_new_message(driver)
                    if haveNewMessage:
                        await telegram_send_notification()

                    time.sleep(240)

                # Close the browser when it's time to close
                driver.find_element(By.XPATH, "//div[@class='status-box']").click()
                driver.find_element(By.XPATH, "//div[@class='online-down']//div[@class='item'][text()='离线']").click()
                time.sleep(2)
                driver.find_element(By.XPATH, "//div[@class='status-box']").click()
                driver.find_element(By.XPATH, "//div[@class='online-down']//div[@class='item'][text()='退出登录']").click()
                time.sleep(2)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='ivu-btn ivu-btn-primary ivu-btn-large']/span[text()='确定']"))).click()
                time.sleep(3)
                driver.quit()
            else:
                # Sleep for a while before checking the time again
                time.sleep(60)
        else:
            print(f'No scheduled times for {current_day}. Waiting for the next day...')
            # Sleep for a while before checking the time again
            time.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
