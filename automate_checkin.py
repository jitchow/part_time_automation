import asyncio
import schedule
from telethon import TelegramClient

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests
import time

# Use your own values from my.telegram.org
api_id = 24923597
api_hash = "7a04f08385f68ff36841b0c65b83be86"
CHANNEL_ID = -4041523708  # -4041523708 kefu -4038638534 test
initial_url = "https://www.ina72.com/"
client = TelegramClient('session', api_id, api_hash)


def get_final_url(initial_url):
    try:
        response = requests.head(initial_url, allow_redirects=True)
        final_url = response.url
        return final_url
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None


# Function to take a screenshot with interaction, controlled scrolling, and full-screen capture
def take_screenshot(url):
    caption = ""
    itdog_url = "https://www.itdog.cn/http/"
    service = Service(executable_path='msedgedriver.exe')
    driver = webdriver.Edge(service=service)
    driver.get(itdog_url)

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Find the input element and submit button
    input_element = driver.find_element(By.ID, 'host')
    submit_button = driver.find_element(By.XPATH, '//button[@onclick="check_form(\'fast\')"]')

    final_url = get_final_url(url)
    # Add text to the input element
    input_element.send_keys(final_url)  # Replace 'example.com' with the desired text

    # Click the submit button
    submit_button.click()
    time.sleep(10)

    china_mobile_span = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//span[@class="custom-control-label2" and text()=" 中国移动"]'))
    )
    # Click the "中国移动" span element
    china_mobile_span.click()
    time.sleep(5)  # Add a delay if needed

    # Find the "time_out" span element
    time_out_span = driver.find_element(By.XPATH, '//span[@class="time_out badge badge-danger small"]')
    # Get the value of the "time_out" span and convert it to an integer
    time_out_value = int(time_out_span.text)

    # Check if the value is more or less than 10
    if time_out_value < 10:
        caption = f"{final_url} 打卡 IP正常运行"
    elif time_out_value >= 10:
        caption = f"{final_url} 打卡 IP运行出现{time_out_value}个错误。"

    # Find the element with class "mt-3" and style "display:flex;"
    element = driver.find_element(By.XPATH, "//div[@class='mt-3' and @style='display:flex;']")
    # Scroll down to the element
    driver.execute_script("arguments[0].scrollIntoView();", element)
    time.sleep(1)  # Add a delay for scrolling to complete

    # Make the page full screen
    driver.maximize_window()
    time.sleep(2)  # Add a delay for maximizing the window

    # Take a screenshot
    driver.save_screenshot('screenshot.png')
    driver.quit()

    return caption


async def send_telegram():
    try:
        caption = take_screenshot(initial_url)
        async with client:
            await client.send_file(CHANNEL_ID, 'screenshot.png', caption=caption)

            if "错误" in caption:
                await client.send_message(CHANNEL_ID, "@Huazai883")
    except Exception as e:
        print(e)

    print('Sent: ' + caption)


def run_async_task(task, loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task)


# def schedule_telegram_messages(times):
#     loop = asyncio.get_event_loop()
#     for t in times:
#         task = send_telegram()
#         schedule.every().day.at(t).do(run_async_task, task, loop)

def schedule_telegram_messages(weekly_schedule):
    loop = asyncio.get_event_loop()
    for day, times in weekly_schedule.items():
        for t in times:
            task = send_telegram()
            getattr(schedule.every().day, day.lower()).at(t).do(run_async_task, task, loop)


if __name__ == "__main__":

    time_ranges = {
        '9amto6pm' : ['09:00', '10:01', '11:05', '12:03', '13:02', '14:04', '15:05', '16:03', '17:02', '18:00'],
        '3pmto9pm' : ['15:00', '16:03', '17:05', '18:02', '19:04', '20:00', '21:00'],
        '6pmto11pm' : ['18:00', '19:03', '20:04', '21:01', '22:05', '23:02'],
        '3pmto9pm_wed' : ['00:03', '01:05', '02:04', '03:00', '15:00', '16:03', '17:05', '18:02', '19:04', '20:00', '21:00']
    }

    scheduled_times = {
        'Monday' : time_ranges['3pmto9pm'],
        'Tuesday' : time_ranges['6pmto11pm'],
        'Wednesday' : time_ranges['3pmto9pm_wed'],
        'Thursday' : time_ranges['3pmto9pm'],
        'Friday' : time_ranges['3pmto9pm'],
        'Saturday' : time_ranges['3pmto9pm'], # update this after 17/2/2024
        # 'Sunday' : time_ranges['9amto6pm'] # delete this after 5/2/2024
    }

    schedule_telegram_messages(scheduled_times)

    while True:
        schedule.run_pending()
        time.sleep(1)