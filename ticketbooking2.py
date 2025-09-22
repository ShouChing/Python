from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from retrying import retry
import time, random, logging, requests, datetime

LOG_PATH = r"C:\Users\User\python\booking_notify.log"
logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

def send_discord(message, webhook_url, success):
    try:
        # 根據成功/失敗選擇顏色和 emoji
        if success:
            color = 0x00ff00  # 綠色
            emoji = "🎟️"
            title = "訂票成功"
        else:
            color = 0xff0000  # 紅色
            emoji = "❌"
            title = "訂票失敗"

        # Discord Embed 格式（比較美觀）
        embed = {
            "title": f"{emoji} {title}",
            "description": message,
            "color": color,
        }

        # 組合資料
        data = {"embeds": [embed]}

        # 發送請求
        response = requests.post(
            webhook_url,
            json=data,
            timeout=10
        )

        if response.status_code != 204:
            logging.error(f"Discord 通知發送失敗: {response.status_code}")
            return False

    except Exception as e:
        logging.error(f"Discord 通知發送錯誤: {e}")
        return False

def notify_user(title, message, success):
    logging.info(f"NOTIFY: {title} - {message}")
    url = ("https://discord.com/api/webhooks/"
           "1418748750918193242/9JQVgRnonXPebJMIDjUm7J4vYFeSlG0amvw42KhK82zjTysdAonz8-XRmVCevF-Owges")
    # Discord 通知
    discord_message = f"**{title}**\n{message}\n⏰ 時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_discord(discord_message, url, success)

def main():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-gpu')
    options.add_argument('--incognito')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    with webdriver.Chrome(options=options) as browser:
        url = 'https://www.railway.gov.tw/tra-tip-web/tip/tip001/tip121/query'
        try:
            browser.get(url)
            browser.find_element(By.CSS_SELECTOR, "a[aria-controls='tab2']").click()
            browser.find_element(By.CSS_SELECTOR, "label[for='seatPref2']").click()
            input_text(browser, 'input.idmember.pid.form-input', '')
            input_text(browser, 'input#rideDate1', '20251006')
            input_text(browser, 'input[placeholder="出發站"]', '4400-高雄')
            input_text(browser, 'input[placeholder="抵達站"]', '1210-新竹')
            input_text(browser, 'input.form-control.input-small.trainNoList.train1', '132')
            browser.find_element(By.CSS_SELECTOR, 'input.btn.btn-3d').click()
        except Exception as e:
            print(f"訂票過程中發生錯誤: {e}")
            logging.error(f"訂票過程中發生錯誤: {e}")
            return  "訂票過程中發生錯誤", e

        try:
            element = browser.find_element(By.CSS_SELECTOR, 'label[for="route00"]')
            human_like_mouse_move(browser, element)
            click_with_delay(element)
        except NoSuchElementException:
            print("沒票了")
            logging.info("沒有找到可訂票的車次")
            return
        except Exception as e:
            print(f"訂票過程中發生錯誤: {e}")
            logging.error(f"訂票過程中發生錯誤: {e}")
            return

        try:
            browser.switch_to.frame(browser.find_element(By.CSS_SELECTOR,
                                                         'iframe[title="google recaptcha"]'))
            captcha_element = browser.find_element(By.CSS_SELECTOR,
                                                   'div.recaptcha-checkbox-border')
            human_like_mouse_move(browser, captcha_element)
            click_with_delay(captcha_element)
            browser.switch_to.default_content()
        except NoSuchElementException:
            pass

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
            logging.info(info.text)
            return info.text
        else:
            print("未找到車票代碼，頁面內容: ")
            print(soup.prettify())

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

@retry(stop_max_attempt_number=3, wait_fixed=1000)
def click_with_delay(element):
    time.sleep(random.uniform(0.5, 2.0))
    element.click()
    time.sleep(random.uniform(0.5, 2.0))

def disable_task(task_name="TRA2"): # 在成功下單後呼叫
    import subprocess
    # 或用 locale.getpreferredencoding(False) 動態取得系統編碼
    system_enc = 'cp950'  # 台灣繁中 Windows 常見
    try:
        res = subprocess.run(
            ['schtasks', '/Change', '/TN', task_name, '/DISABLE'],
            capture_output=True, text=True, encoding=system_enc, timeout=10
        )
    except Exception as e:
        logging.error(f"禁用排程時執行 subprocess 失敗: {e}")
        return False

    if res.stdout:
        logging.info(f"schtasks stdout: {res.stdout.strip()}")
        print(res.stdout.strip())   # 或顯示給使用者
    if res.stderr:
        logging.error(f"schtasks stderr: {res.stderr.strip()}")
        print(res.stderr.strip())

def in_current_window(now=None):
    if now is None:
        now = datetime.datetime.now()
    hour_start = now.replace(minute=0, second=0, microsecond=0)
    window_end = hour_start + datetime.timedelta(minutes=5, seconds=30)
                                                   # 3. 計算視窗結束時間（整點 + WINDOW_MINUTES + WINDOW_SECONDS_EXTRA）
    return hour_start <= now <= window_end

result = main()
while in_current_window():
    if type(result) is tuple:
        notify_user(result[0], result[1], success=False)
        break
    elif result:
        disable_task()
        notify_user("訂票成功", f"車票代碼: {result}", success=True)
        print("已訂到票，已停用排程。")
        break

    time.sleep(30)
    result = main()
else:
    notify_user("訂票未成功", "本次嘗試未找到票，排程仍會繼續", success=False)