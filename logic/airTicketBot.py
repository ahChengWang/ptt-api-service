# from telegram import InlineKeyboardMarkup, Update
# from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
from dotenv import load_dotenv
import os
import json


def __init__(self) -> None:
    self.ENV = os.getenv("ENV", "PRD")  # 預設為 production
    if self.ENV == 'DEV':
        load_dotenv()  # 本機執行時載入 .env

    self.loc_list = json.loads(os.getenv("START_LOCATIONS"))
    self.TG_TOKEN = os.getenv("TG_TOKEN")
    self.TG_CHAT_ID = os.getenv("TG_CHAT_ID")


def start_loc(self) -> str:

    # 建立 inline keyboard 按鈕，每行一個
    buttons = [
        [{"text": f"📍 {loc['title']}", "callback_data": f"select_start::{loc_id}"}]
        for loc_id, loc in self.loc_list.items()
    ]

    message_payload = {
        "chat_id": self.TG_CHAT_ID,
        "text": "<b>✈ 請選擇一個出發地點：</b>",
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": buttons
        }
    }

    resp = requests.post(
        f"https://api.telegram.org/bot{self.TG_TOKEN}/sendMessage", json=message_payload)

    return resp
