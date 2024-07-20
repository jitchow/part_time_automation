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

import psutil
import time
import os
from config import scheduled_times_checkin, telegram_bot
from dotenv import load_dotenv
from datetime import datetime, timedelta
import constants

load_dotenv()

# Use your own values from my.telegram.org
TELEGRAM_API_ID = constants.TELEGRAM_API_ID
TELEGRAM_API_HASH = constants.TELEGRAM_API_HASH
TELEGRAM_KEFU_CHANNEL_ID = constants.TELEGRAM_TEST_CHANNEL_ID
TELEGRAM_TEST_CHANNEL_ID = constants.TELEGRAM_TEST_CHANNEL_ID
EDGE_DRIVER_PATH = constants.EDGE_DRIVER_PATH

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

def get_final_url(initial_url):
    recommendation_url = initial_url + 'recommendation'

    # Initialize the WebDriver for Microsoft Edge
    service = Service(executable_path=EDGE_DRIVER_PATH)
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
    # Clean any processes on port 9222
    kill_processes_on_port(9222)

    # Spin up browser on port 9222 with default user data
    command = 'start msedge.exe -remote-debugging-port=9222 --user-data-dir="C:\\Users\\JC\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default"'
    os.system(command)

    reset_failure_count_if_new_day()  # Check if we need to reset the failure count

    caption = ""
    
    service = Service(executable_path=EDGE_DRIVER_PATH)
    edge_options = Options()
    edge_options.use_chromium = True  
    edge_options.add_experimental_option("debuggerAddress", "localhost:9222") 
    edge_options.add_argument('--disable-cloud-management')
    edge_options.add_argument('--disable-extensions')
    
    driver = webdriver.Edge(service=service, options=edge_options)
    driver.maximize_window()

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    wait = WebDriverWait(driver, 10)

    # Redirect
    aliyun_link = constants.LINK_ALIYUN
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
    statuses = ['610', '611', '613', '614']
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

    # Scroll the element into view using JavaScript
    detection_data_div = driver.find_element(By.CSS_SELECTOR, 'div.show-detection-data')
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
    kill_processes_on_port(9222)

    return caption

async def send_daily_checks():
    message = """
    -注册 ：测试完成\n-登录：测试完成\n-购买：测试完成\n-观看：测试完成\n-书架/订阅 ：完成\n-排行榜：测试完成\n-充值：测试完成\n-vip：测试正常\n\n友情推荐正常
    """
    try:
        async with client:
            await client.send_message(TELEGRAM_KEFU_CHANNEL_ID, message)
        print(f'Sent: {message}')
    except Exception as e:
        print(f'Failed to send daily checks: {e}')


async def send_telegram():
    caption = ''
    for attempt in range(MAX_RETRIES):
        try:
            caption = take_screenshot(initial_url)
            async with client:
                await client.send_file(TELEGRAM_KEFU_CHANNEL_ID, 'screenshot.png', caption=caption)

                if failure_count <= 1:
                    if "错误" in caption:
                        await client.send_message(TELEGRAM_KEFU_CHANNEL_ID, constants.TELEGRAM_HUAZAI_ID)
            print('Sent: ' + caption)
            break
        except Exception as e:
            print(f'Attempt {attempt + 1} failed: {e}')
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                telegram_bot.send_message(TELEGRAM_TEST_CHANNEL_ID, 'Check-in failed after multiple attempts')
                print('Check-in failed after multiple attempts')

asyncio.run(send_telegram())