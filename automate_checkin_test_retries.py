import asyncio
import schedule
from telethon import TelegramClient

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options

import requests
import time
import os
import psutil
from config import scheduled_times_checkin, telegram_bot
from datetime import datetime
import constants

# Use your own values from my.telegram.org
TELEGRAM_API_ID = constants.TELEGRAM_API_ID
TELEGRAM_API_HASH = constants.TELEGRAM_API_HASH
TELEGRAM_KEFU_CHANNEL_ID = constants.TELEGRAM_KEFU_CHANNEL_ID
TELEGRAM_TEST_CHANNEL_ID = constants.TELEGRAM_TEST_CHANNEL_ID

telegram_client = TelegramClient('session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
LAST_CHECKED_DAY = datetime.now().day

MAX_RETRIES = 3
RETRY_DELAY = 5  # in seconds

def get_final_url(initial_url):
    response = requests.get(initial_url, allow_redirects=True)
    return response.url

def kill_processes_on_port(port):
    # Get a list of all processes
    processes = psutil.process_iter(['pid', 'name', 'connections'])
    
    for proc in processes:
        try:
            # Iterate over connections of each process
            for conn in proc.info['connections']:
                if conn.laddr.port == port:
                    print(f"Killing process {proc.info['name']} (PID: {proc.info['pid']}) on port {port}")
                    proc.terminate()
                    proc.wait()  # Wait for the process to be terminated
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass

# Function to take a screenshot with interaction, controlled scrolling, and full-screen capture
def take_screenshot(website, url):
    # Clean any processes on port 9222
    kill_processes_on_port(9222)

    # Spin up browser on port 9222 with default user data
    command = 'start msedge.exe -remote-debugging-port=9222 --user-data-dir="C:\\Users\\JC\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default"'
    os.system(command)

    caption = ""
    
    service = Service(executable_path=constants.EDGE_DRIVER_PATH)
    edge_options = Options()
    edge_options.use_chromium = True  
    edge_options.add_experimental_option("debuggerAddress", "localhost:9222") 
    edge_options.add_argument('--disable-cloud-management')
    edge_options.add_argument('--disable-extensions')
    
    driver = webdriver.Edge(service=service, options=edge_options)
    driver.get(constants.LINK_ITDOG)

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    wait = WebDriverWait(driver, 10)

    # Find the input element and submit button
    input_element = driver.find_element(By.ID, 'host')
    submit_button = driver.find_element(By.XPATH, '//button[@onclick="check_form(\'fast\')"]')

    final_url = get_final_url(url)
    # Add text to the input element
    input_element.send_keys(final_url) 

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
        caption = f"{final_url} {website} 正常运行"
    elif time_out_value >= 10:
        caption = f"{final_url} {website} {time_out_value}错误"

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
    kill_processes_on_port(9222)
    
    return caption, time_out_value

async def send_telegram():
    tag_huazai_flag = False
    caption = ''

    for website, url in constants.INS_AV_WEBSITES.items():
        for attempt in range(MAX_RETRIES):
            try:
                caption, time_out_value = take_screenshot(website, url)

                if time_out_value >= 30:
                    tag_huazai_flag = True

                async with telegram_client:
                    await telegram_client.send_file(TELEGRAM_KEFU_CHANNEL_ID, 'screenshot.png', caption=caption)

                print('Sent: ' + caption)
                break
            except Exception as e:
                print(f'Attempt {attempt + 1} failed: {e}')
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    telegram_bot.send_message(TELEGRAM_TEST_CHANNEL_ID, 'Check-in failed after multiple attempts')
                    print('Check-in failed after multiple attempts')

        
    if tag_huazai_flag == True:
        async with telegram_client:
            await telegram_client.send_message(TELEGRAM_KEFU_CHANNEL_ID, constants.TELEGRAM_HUAZAI_ID)

def run_async_task(task, loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task)

def schedule_telegram_messages(weekly_schedule):
    loop = asyncio.get_event_loop()
    for day, times in weekly_schedule.items():
        for t in times:
            task = send_telegram()
            getattr(schedule.every().day, day.lower()).at(t).do(run_async_task, task, loop)

if __name__ == "__main__":
    try:
        schedule_telegram_messages(scheduled_times_checkin)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        telegram_bot.send_message(TELEGRAM_TEST_CHANNEL_ID, f'Check-in crashed: {e}')
        print(f'Check-in crashed: {e}')
