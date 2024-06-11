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
import os
from config import scheduled_times_checkin, telegram_bot
from dotenv import load_dotenv
load_dotenv()

# Use your own values from my.telegram.org
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_KEFU_CHANNEL_ID = int(os.getenv('TELEGRAM_KEFU_CHANNEL_ID'))
TELEGRAM_TEST_CHANNEL_ID = int(os.getenv('TELEGRAM_TEST_CHANNEL_ID'))

initial_url = "https://www.inb619.com/"

client = TelegramClient('session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
failure_count = 0

def get_final_url(initial_url):
    response = requests.head(initial_url, allow_redirects=True)
    final_url = response.url

    recommendation_url = final_url + 'recommendation'

    # Initialize the WebDriver for Microsoft Edge
    service = Service(executable_path=os.getenv('EDGE_DRIVER_PATH'))
    options = webdriver.EdgeOptions()
    options.add_argument('--headless')  # Run in headless mode (without opening a browser window)
    driver = webdriver.Edge(service=service, options=options)

    try:
        # Open the webpage
        driver.get(recommendation_url)
        
        # Wait for the element to be present
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='禁漫']/parent::a"))
        )

        # Get the link from the 'href' attribute of the parent 'a' tag
        final_url = element.get_attribute('href')
        return final_url

    finally:
        driver.quit()


# Function to take a screenshot with interaction, controlled scrolling, and full-screen capture
def take_screenshot(url):
    caption = ""
    itdog_url = os.getenv('LINK_ITDOG')
    
    service = Service(executable_path=os.getenv('EDGE_DRIVER_PATH'))
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

    global failure_count
    # Check if the value is more or less than 10
    if time_out_value < 10:
        failure_count = 0
        caption = f"{final_url} 打卡 IP正常运行"
    elif time_out_value >= 10:
        failure_count += 1
        if failure_count <= 1:
            caption = f"{final_url} 打卡 IP运行出现{time_out_value}个错误"
        else:
            caption = f"{final_url} 出现{time_out_value}个错误 等待修复"

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
    caption = ''
    caption = take_screenshot(initial_url)

    async with client:
        await client.send_file(TELEGRAM_KEFU_CHANNEL_ID, 'screenshot.png', caption=caption)

        if failure_count <= 1:
            if "错误" in caption:
                await client.send_message(TELEGRAM_KEFU_CHANNEL_ID, "@Hzai5522")

    print('Sent: ' + caption)


def run_async_task(task, loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task)


def schedule_telegram_messages(weekly_schedule):
    loop = asyncio.get_event_loop()
    for day, times in weekly_schedule.items():
        for t in times:
            task = send_telegram()
            getattr(schedule.every().day, day.lower()).at(t).do(run_async_task, task, loop)


try:
    if __name__ == "__main__":
        schedule_telegram_messages(scheduled_times_checkin)

        while True:
            schedule.run_pending()
            time.sleep(1)
except:
    # Cancel all tasks
    schedule.clear()
    telegram_bot.send_message(TELEGRAM_TEST_CHANNEL_ID, 'Check-in crashed.....')
    print('Check-in crashed.....')
