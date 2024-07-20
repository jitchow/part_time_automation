import asyncio
import schedule
from telethon import TelegramClient

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options

import requests
import subprocess
import time
import os
from config import scheduled_times_checkin, telegram_bot
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Use your own values from my.telegram.org
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_KEFU_CHANNEL_ID = int(os.getenv('TELEGRAM_KEFU_CHANNEL_ID'))
TELEGRAM_TEST_CHANNEL_ID = int(os.getenv('TELEGRAM_TEST_CHANNEL_ID'))

initial_url = "https://jm18.me/"

client = TelegramClient('session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
failure_count = 0
last_checked_day = datetime.now().day

MAX_RETRIES = 3
RETRY_DELAY = 5  # in seconds

def reset_failure_count_if_new_day():
    global failure_count, last_checked_day
    current_day = datetime.now().day
    current_time = datetime.now().strftime('%H:%M')

    if current_day != last_checked_day and current_time > '03:05':
        failure_count = 0
        last_checked_day = current_day

def get_final_url(initial_url):
    recommendation_url = initial_url + 'recommendation'

    # Initialize the WebDriver for Microsoft Edge
    msedge_path = os.path.join(os.getcwd(), os.getenv('EDGE_DRIVER_PATH'))
    service = Service(executable_path=msedge_path)
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
    reset_failure_count_if_new_day()  # Check if we need to reset the failure count

    caption = ""
    aliyun_zh_link = os.getenv('LINK_ALIYUN_ZH')
    
    msedge_path = os.path.join(os.getcwd(), os.getenv('EDGE_DRIVER_PATH'))
    service = Service(executable_path=msedge_path)
    edge_options = Options()
    edge_options.use_chromium = True  
    edge_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")  
    edge_options.add_argument('--disable-cloud-management')
    edge_options.add_argument('--disable-extensions')
    driver = webdriver.Edge(service=service, options=edge_options)

    # driver.get(aliyun_zh_link)

    driver.maximize_window()

    wait = WebDriverWait(driver, 10)
    # WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
   

    # Wait until the language menu is present
    # WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, "ul.langs-wrap"))
    # )
    # # Click the <span> element containing "简体中文"
    # driver.execute_script("document.querySelector('a[data-lang=\"zh\"] span').click();")
    # time.sleep(30)

    # Redirect
    aliyun_link = os.getenv('LINK_ALIYUN')
    driver.get(aliyun_link)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    final_url = get_final_url(url)
    # Input the URL into the text field
    url_input = wait.until(EC.presence_of_element_located((By.ID, "url1")))
    url_input.send_keys(final_url)

    # Click the "OK" button
    ok_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@class='next-btn next-large next-btn-primary pramary-button' and @data-spm-click='gostr=/aliyun;locaid=search']")))
    ok_button.click()

    time.sleep(20)

    # Click on the label with the text "Operator"
    operator_label = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//label[text()='运营商']"))
    )
    operator_label.click()

    # Wait for the dropdown options to be available and select the "China-Mobile" option
    china_mobile_option = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//li[@role='option' and @title='移动']"))
    )
    china_mobile_option.click()
    time.sleep(5)

    # Find number of http status 611, 613 and 614
    statuses = ['611', '613', '614']
    time_out_value = 0

    for status in statuses:
        status_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{status}')]")
        time_out_value += len(status_elements)

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

    detection_data_div = driver.find_element(By.CSS_SELECTOR, 'div.show-detection-data')
    # Scroll the element into view using JavaScript
    driver.execute_script("arguments[0].scrollIntoView(true);", detection_data_div)
    time.sleep(2)  # Add a delay for scrolling to complete

    # Click on the "status" element
    status_icon = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//span[@role='button' and contains(@class, 'next-table-sort next-table-header-icon')]"))
    )
    status_icon.click()

    # Take a screenshot
    driver.save_screenshot('screenshot.png')
    driver.quit()

    return caption

async def send_telegram():
    caption = ''
    for attempt in range(MAX_RETRIES):
        try:
            caption = take_screenshot(initial_url)
            async with client:
                await client.send_file(TELEGRAM_TEST_CHANNEL_ID, 'screenshot.png', caption=caption)

                if failure_count <= 1:
                    if "错误" in caption:
                        await client.send_message(TELEGRAM_TEST_CHANNEL_ID, "@Hzai5522")
            print('Sent: ' + caption)
            break
        except Exception as e:
            print(f'Attempt {attempt + 1} failed: {e}')
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                telegram_bot.send_message(TELEGRAM_TEST_CHANNEL_ID, 'Check-in failed after multiple attempts')
                print('Check-in failed after multiple attempts')

command = 'start msedge.exe -remote-debugging-port=9222 --user-data-dir="C:\\Users\\JC\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default"'
# Execute the command
os.system(command)

asyncio.run(send_telegram())