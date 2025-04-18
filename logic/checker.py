import os
import requests
from bs4 import BeautifulSoup
import time

PTT_URL = "https://www.pttweb.cc/bbs/Lifeismoney?m=0"
HEADERS = {
    "cookie": "over18=1",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/134.0.0.0 Safari/537.36"
    )
}
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
STATE_FILE = "last_sent.txt"


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    res = requests.post(url, data=data)
    time.sleep(2)
    return res.ok


def load_last_urls():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_last_urls(url):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(url)


def check_new_posts():
    last_url = load_last_urls()
    res = requests.get(PTT_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    latest_title = ""

    containers = soup.select("div.e7-container")
    new_info_articles = []

    for container in containers:
        type_tag = container.select_one("div.e7-type")
        title_tag = container.select_one("span.e7-title span")
        link_tag = container.select_one("a.e7-article-default")

        if not (type_tag and title_tag and link_tag):
            continue

        if "情報" not in type_tag.text.strip() or "全台捐血" in link_tag.text.strip():

            continue

        full_url = "https://www.pttweb.cc" + link_tag["href"]
        title = title_tag.text.strip()

        if full_url == last_url:
            latest_title = title
            break

        new_info_articles.append((title, full_url))

    if not new_info_articles:
        print("🔁 無新 [情報] 文章:近一篇 " + latest_title)
        return

    # 發送推播（最舊的在前）
    for title, url in reversed(new_info_articles):
        message = f"<b><b>🌟[情報更新]🌟</b></b>\n{title}\n{url}"

        # send_telegram_message(message)

    # 記錄最新一篇文章
    latest_sent_url = new_info_articles[0][1]
    save_last_urls(latest_sent_url)

    return [url for _, url in new_info_articles]
