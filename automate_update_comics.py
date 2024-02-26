from langdetect import detect
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from tqdm import tqdm

# from / back
MODE = 'back'
PAGES_TO_DO = 1

categories = {
    '剧情韩漫': 1,
    '耽美漫画': 3,
    '真人漫画': 4,
    '校园漫画': 5,
    '日韩漫画': 6,
    '少女漫画': 8,
    '恋爱漫画': 9
}


def select_category(title, desc):
    try:
        if any(keyword in title or keyword in desc for keyword in ['学', '校', '教', '师']):
            return categories['校园漫画']
        elif any(keyword in title or keyword in desc for keyword in ['cosplay']):
            return categories['真人漫画']
        elif any(keyword in title or keyword in desc for keyword in ['女']):
            return categories['少女漫画']
        elif any(keyword in title or keyword in desc for keyword in ['爱']):
            return categories['恋爱漫画']
        elif detect(title) == 'ja' or detect(desc) == 'ja':
            return categories['日韩漫画']
        else:
            return categories['剧情韩漫']
    except:
        return categories['剧情韩漫']


url = "https://madmin.9xyrp3kg4b86.com/index/index"
driver = webdriver.Edge(service=Service(executable_path='msedgedriver.exe'))

try:
    driver.get(url)
    driver.maximize_window()

    driver.find_element(By.ID, "username").send_keys("xiaoyu")
    driver.find_element(By.ID, "password").send_keys("qweqwe")
    driver.find_element(By.XPATH, "//input[@value='登录']").click()

    time.sleep(2)

    driver.find_element(By.XPATH, "//a[contains(., '漫画管理')]").click()
    time.sleep(1)
    driver.find_element(By.XPATH, "//a[contains(., '漫画列表')]").click()

    time.sleep(2)
    iframe_tab_id = "c92761fd166a5c85385340d8c1a3f456"
    driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, f"iframe[tab-id='{iframe_tab_id}']"))

    driver.find_element(By.XPATH, "//input[@placeholder='选择状态']").click()
    time.sleep(1)
    driver.find_element(By.XPATH, "//dd[@lay-value='0']").click()

    driver.find_element(By.XPATH, "//input[@value='搜索']").click()
    time.sleep(2)

    driver.find_element(By.XPATH, "//span[@class='layui-laypage-limits']//select").click()
    driver.find_element(By.XPATH, "//option[@value='100']").click()
    time.sleep(2)

    if MODE == 'back':
        driver.find_element(By.XPATH, "//a[@class='layui-laypage-last']").click()

    for page in tqdm(range(PAGES_TO_DO), desc="Updating Page", unit="page"):
        if MODE == 'back':
            if page != 0:
                driver.find_element(By.XPATH, "//a[@class='layui-laypage-prev']").click()
                time.sleep(2)
                driver.find_element(By.XPATH, "//a[@class='layui-laypage-next']").click()
                time.sleep(2)

                driver.switch_to.default_content()
                iframe_tab_id = "c92761fd166a5c85385340d8c1a3f456"
                driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, f"iframe[tab-id='{iframe_tab_id}']"))

            # Get the total count from the span element
            total_count = int(''.join(filter(str.isdigit, driver.find_element(By.CLASS_NAME, "layui-laypage-count").text)))
            # Extract the last two digits using modulo operator
            last_two_digits = total_count % 100
            if last_two_digits == 0:
                last_two_digits = 100

        elif MODE == 'front':
            last_two_digits = 100

        for comic in tqdm(range(last_two_digits), desc="Updating Comics", unit="comic"):
            try:
                first_row = driver.find_element(By.XPATH, "//tbody/tr[1]")
                first_row.find_element(By.XPATH, "//button[contains(@onclick, 'set_edit')]").click()

                time.sleep(1)
                iframe = driver.find_element(By.ID, "layui-layer-iframe1")
                driver.switch_to.frame(iframe)

                title_value = driver.find_element(By.NAME, "title").get_attribute("value") or ''
                desc_value = driver.find_element(By.ID, "desc").get_attribute("value") or ''
                category_index = select_category(title=title_value, desc=desc_value)

                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='选择题材']"))).click()
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, f"//dd[@lay-value='{category_index}']"))).click()

                driver.find_element(By.XPATH, "//div[text()='正常']").click()
                driver.find_element(By.CSS_SELECTOR, "div.layui-input-block button").click()

                time.sleep(2)

                driver.switch_to.default_content()
                iframe_tab_id = "c92761fd166a5c85385340d8c1a3f456"
                driver.switch_to.frame(driver.find_element(By.CSS_SELECTOR, f"iframe[tab-id='{iframe_tab_id}']"))
                time.sleep(1)
            except Exception as e:
                comic -= 1
                continue

finally:
    print()
    print("--------------------DONE AND DUSTED--------------------")
    print()
    driver.quit()
