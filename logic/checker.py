import os
import requests
import time
import json
from bs4 import BeautifulSoup
import subprocess
import cloudscraper
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By


class checker():

    def __init__(self) -> None:

        self.ENV = os.getenv("ENV", "PRD")  # 預設為 production
        if self.ENV == 'DEV':
            load_dotenv()  # 本機執行時載入 .env

        self.PTT_URL = "https://www.ptt.cc/bbs/Lifeismoney/index.html"
        self.DCARD_URL = "https://www.dcard.tw/service/api/v2/globalPaging/page?enrich=true&forumLogo=true&pinnedPosts=widget&country=TW&platform=web&listKey=f_latest_817d71bb-ebdf-4326-b8aa-10df4fcdf03a&immersiveVideoListKey=v_latest_817d71bb-ebdf-4326-b8aa-10df4fcdf03a&pageKey=f_latest_817d71bb-ebdf-4326-b8aa-10df4fcdf03a&offset=0"
        self.HEADERS = {
            "cookie": "over18=1",
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
                           ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Connection": "keep-alive",
            "Cookie": "_gid=GA1.2.951163347.1744857895; _ga_DZ6Y3BY9GW=GS1.1.1744887842.171.1.1744887842.0.0.0; _ga=GA1.2.1231348713.1606230154; cf_clearance=C5t15vY8Ic4rcFYVc8wT4qplXpLAeXHC17TyE6abueo-1744887843-1.2.1.1-.pbW1QYvzjnrD.STJsIis52f6PMq958qqmhXOpakyst.TpGMk2t2g95di9jR0wsQyaDCfifM6rqsKkhjc10JJdrk0PqbWb_f_8FuxFP2mEOFH55pFozw8PH4hHjYqpsRDYbhtLvbJzZTcz0S2QZ4dLpnHN_wZmPYE4HiirUOcE8FhFjkpGeC__bfBgQVGdYqzi2S5u_JaAFtfvMUK6qnRDwCdN15DA_0et_aZNY1.0IFsTeQ2cqniR6LW68DG96x64JZ91uUGLOI1hExtqLTvhgIRuH6A474_rkMdogYX3nlTAssypyjs3nWnP4fOqddIvdO904A1D34o0UI0uJ72jfYnvFk9Knv1q4MhvjqsEI"
        }
        self.TG_TOKEN = os.getenv("TG_TOKEN")
        self.TG_CHAT_ID = os.getenv("TG_CHAT_ID")
        self.STATE_FILE = "last_sent.txt"
        # 讀取 JSON 字串並轉成 dict
        # self.CREDS_JSON = json.loads(os.environ["GSHEET_CREDS_JSON"])
        self.CREDS_JSON = json.loads(os.getenv("SHEET_CRED"))

        # 建立憑證物件
        self.CREDS = Credentials.from_service_account_info(
            self.CREDS_JSON, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        # 建立 gspread client
        self.CLIENT = gspread.authorize(self.CREDS)
        # 讀取 sheet
        self.SHEET = self.CLIENT.open_by_key(os.getenv("LAST_SEND_ID")).sheet1

    def send_telegram_message(self, message):
        url = f"https://api.telegram.org/bot{self.TG_TOKEN}/sendMessage"
        data = {
            "chat_id": self.TG_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ 已推送 Telegram")
        else:
            print("❌ 傳送失敗：", response.text)
        time.sleep(3)

    def load_last_urls(self) -> str:
        # 讀取/寫入操作
        return self.SHEET.acell("A1").value

        # if not os.path.exists(STATE_FILE):
        #     return None
        # with open(STATE_FILE, "r", encoding="utf-8") as f:
        #     return f.read().strip()

    def save_last_urls(self, url: str):
        self.SHEET.update("A1", [[url]])
        # with open(STATE_FILE, "w", encoding="utf-8") as f:
        #     f.write(url)

    def check_new_posts(self):
        last_url = self.load_last_urls()
        print("last_url=" + last_url)
        scraper = cloudscraper.create_scraper()  # 模擬瀏覽器
        res = scraper.get(self.PTT_URL, headers=self.HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        latest_title = ""
        print("soup=" + str(soup.text).replace('\n\n\n', ''))
        containers = soup.select("div.title a")

        new_info_articles = []

        if not containers:
            print("⚠️ 找不到文章")
            return

        found_last = False

        # 收集最新文章，逆序排列（最舊的先推）
        for tag in reversed(containers):
            title = tag.text.strip()
            relative_link = tag['href']
            full_url = "https://www.ptt.cc" + relative_link

            if "情報" not in title.strip() or "全台捐血" in title.strip():
                continue

            latest_title = title
            if full_url == last_url:
                found_last = True
                break
            else:
                new_info_articles.append((title, full_url))

        if not new_info_articles:
            print("🔁 無新 [情報] 文章:近一篇 " + latest_title)
            return

        # 發送推播（最舊的在前）
        for title, url in reversed(new_info_articles):
            message = f"<b><b>🌟[情報更新]🌟</b></b>\n{title}\n{url}"

            self.send_telegram_message(message)

        # 記錄最新一篇文章
        latest_sent_url = new_info_articles[0][1]
        self.save_last_urls(latest_sent_url)

        return [url for _, url in new_info_articles]

    # def get_dcard_latest_posts(self, last_url_dcard: str) -> list:
    #     # 建立瀏覽器選項
    #     options = Options()
    #     options.add_argument('--headless')  # 無頭模式
    #     options.add_argument('--disable-gpu')
    #     options.add_argument('--no-sandbox')
    #     options.add_argument('--window-size=1920,1080')
    #     options.add_argument('--disable-dev-shm-usage')
    #     options.add_argument(
    #         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    #     # 啟動 Selenium
    #     driver = webdriver.Chrome(service=Service(
    #         ChromeDriverManager().install()), options=options)

    #     # 前往省錢版最新文章頁面
    #     url = "https://www.dcard.tw/f/savemoney?tab=latest"
    #     driver.get(url)
    #     time.sleep(15)  # 等待 JavaScript 渲染

    #     # 抓出所有文章卡片
    #     posts = driver.find_elements(
    #         By.CSS_SELECTOR, "a[href^='/f/savemoney/p/']")

    #     for post in posts[:5]:  # 前5篇
    #         try:
    #             title_element = post.find_element(By.CSS_SELECTOR, "h2")
    #             link_element = post.find_element(
    #                 By.CSS_SELECTOR, "a[href^='/f/savemoney/p/']")
    #             title = title_element.text.strip()
    #             url = "https://www.dcard.tw" + \
    #                 link_element.get_attribute("href")
    #             print(f"{title}\n{url}\n")
    #         except Exception as e:
    #             continue

    #     driver.quit()

    #     return []
