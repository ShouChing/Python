from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time, random, logging, sys, os
# -*- coding: utf-8 -*-

# Tkinter 用於跳出視窗
try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog
    _HAS_TK = True
except Exception:
    _HAS_TK = False
LOG_PATH = r"C:\Users\User\python\booking_notify.log"
logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

def notify_user(title, message, success=False, require_input=False, timeout=10):
    logging.info(f"NOTIFY: {title} - {message}")

    # 检查是否在无头环境或任务计划程序环境中运行
    is_headless = os.environ.get('HEADLESS', '0') == '1' or 'SCHTASKS' in os.environ

    if not is_headless:
        # 在任务计划程序环境中，尝试使用其他通知方式
        try:
            # 尝试使用系统通知（如果可用）
            if sys.platform.startswith('win'):
                # Windows 系统通知
                subprocess.run(['powershell', '-command',
                                f'[System.Windows.Forms.MessageBox]::Show("{message}", "{title}")'],
                               timeout=timeout, capture_output=True)
        except Exception as e:
            logging.warning(f"系統通知失敗: {e}")

    # 只有在有图形界面的环境中才使用 Tkinter
    if _HAS_TK and not is_headless:
        try:
            root = tk.Tk()
            root.withdraw()  # 隱藏主視窗
            # 放到最前（避免被其他視窗蓋住）
            root.attributes("-topmost", True)
            # 若需要使用者輸入（例如按確認/輸入），用 simpledialog
            if require_input:
                response = simpledialog.askstring(title, message, parent=root)
                root.destroy()
                logging.info(f"User input response: {response}")
                return response
            else:
                if success:
                    messagebox.showinfo(title, message, parent=root)
                else:
                    messagebox.showerror(title, message, parent=root)
                root.destroy()
                return None
        except Exception as e:
            logging.warning(f"tkinter notify failed: {e}")

    logging.info(f"Fallback notify (log): {title} - {message}")
    
    return None

def main():
    browser = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--incognito')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        browser = webdriver.Chrome(options=options)
        browser.implicitly_wait(30)

        url = 'https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip121/query'
        browser.get(url)
        browser.find_element(By.CSS_SELECTOR, "a[aria-controls='tab2']").click()
        browser.find_element(By.CSS_SELECTOR, "label[for='seatPref2']").click()
        input_text(browser, 'input.idmember.pid.form-input', '')
        input_text(browser, 'input#rideDate1', '20251003')
        input_text(browser, 'input[placeholder="出發站"]', '1210-新竹')
        input_text(browser, 'input[placeholder="抵達站"]', '4400-高雄')
        input_text(browser, 'input.form-control.input-small.trainNoList.train1', '145')
        browser.find_element(By.CSS_SELECTOR, 'input.btn.btn-3d').click()

        element = browser.find_element(By.CSS_SELECTOR, 'label[for="route00"]')

        ActionChains(browser).move_to_element(element).click().perform()
        browser.switch_to.frame(browser.find_element(By.CSS_SELECTOR,
                                                     'iframe[title="google recaptcha"]'))
        captcha_element = browser.find_element(By.CSS_SELECTOR,
                                                     'div.recaptcha-checkbox-border')
        human_like_mouse_move(browser, captcha_element)
        click_with_delay(captcha_element)
        browser.switch_to.default_content()
        element = WebDriverWait(browser, 10).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[type="submit"]')
        ))
        ActionChains(browser).move_to_element(element).click().perform()

        WebDriverWait(browser, 15).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'span.font18')
        ))
        r = browser.page_source
        soup = BeautifulSoup(r, 'html.parser')
        info = soup.select_one('span.font18')

        if info:
            print('車票代碼: ', info.text)
            return info.text
        else:
            print("未找到車票代碼，頁面內容: ")
            print(soup.prettify())
    except NoSuchElementException:
        print("沒票了")
        logging.info("沒有找到可訂票的車次")
        return
    except Exception as e:
        print(f"訂票過程中發生錯誤: {e}")
        logging.error(f"訂票過程中發生錯誤: {e}")
        return None
    finally:
        # 確保瀏覽器總是被關閉
        if browser is not None:
            browser.quit()

def input_text(browser, i1, i2):
    element = browser.find_element(By.CSS_SELECTOR, i1)
    element.click()
    element.clear()
    element.send_keys(i2)

def human_like_mouse_move(browser, element):
    action = ActionChains(browser)
    action.move_to_element_with_offset(element, 5, 5)
    action.move_by_offset(15, 14)
    action.move_by_offset(-16, -15)
    action.perform()

def click_with_delay(element):
    time.sleep(random.uniform(0.5, 2.0))
    element.click()
    time.sleep(random.uniform(0.5, 2.0))

result = main()

import subprocess
# 在成功下單後呼叫
def disable_task(task_name="TRA_Ticket_Booker"):
    # disable
    subprocess.run(['schtasks', '/Change', '/TN', task_name, '/DISABLE'], shell=False)
    # 或直接刪除 (強制)
    # subprocess.run(['schtasks', '/Delete', '/TN', task_name, '/F'], shell=False)

if result:
    disable_task()
    notify_user("訂票成功", f"車票代碼: {result}", success=True, require_input=False)
    print("已訂到票，已停用排程。")
else:
    notify_user("訂票未成功", "本次嘗試未找到票，排程仍會繼續", success=False, require_input=False)
    print("本次嘗試未成功。")