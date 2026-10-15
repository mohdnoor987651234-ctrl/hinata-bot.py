#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import time
import json
import os
import pyotp
import uuid
from flask import Flask
import threading

# ==========================================
# Configuration
# ==========================================
TOKEN = "8510543770:AAEHSpib5zdObv1F1MLKReQhVmrkERTlKFE"
ADMIN_ID = 8438207365
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
DB_FILE = "database.json"
tg_session = requests.Session()

# Flask App for Render Web Service Port Binding
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Premium Emojis
PEM = {
  "ok": '✅',
  "no": '❌',
  "warn": '⚠️',
  "admin": '📊',
  "user": '👤',
  "money": '💸',
  "gift": '🎁',
  "msg": '💬',
  "hi": '👋'
}

# Databases
users = {}
submissions = []
rates = {"ig_2fa": 3.00, "fb_cookies": 4.50}
admin_settings = {
    "supportUrl": "https://t.me/EasyIncomeX_Support",
    "withdrawMethods": [{"name": "bKash", "minAmount": 50}, {"name": "Nagad", "minAmount": 50}],
    "referralTasksRequired": 5,
    "referralBonusAmount": 10.0
}
user_states = {}

def load_db():
    global users, submissions, rates, admin_settings
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                users = {int(k): v for k, v in data.get("users", {}).items()}
                submissions = data.get("submissions", [])
                rates = data.get("rates", rates)
                admin_settings = data.get("admin_settings", admin_settings)
        except:
            pass

def save_db():
    data = {
        "users": {str(k): v for k, v in users.items()},
        "submissions": submissions,
        "rates": rates,
        "admin_settings": admin_settings
    }
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except:
        pass

def is_admin(chat_id):
    if str(chat_id) == str(ADMIN_ID): return True
    return int(chat_id) in admin_settings.get("admins", [])

def api_call(method, payload=None):
    url = f"{BASE_URL}/{method}"
    try:
        if payload:
            res = tg_session.post(url, json=payload, timeout=60)
        else:
            res = tg_session.get(url, timeout=60)
        return res.json()
    except Exception:
        return {}

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api_call("sendMessage", payload)

def getMainMenu():
    return {
        "keyboard": [
            [{"text": "Work"}, {"text": "Balance"}],
            [{"text": "Withdraw"}, {"text": "Support"}]
        ],
        "resize_keyboard": True
    }

def process_updates():
    offset = 0
    load_db()
    while True:
        try:
            res = api_call("getUpdates", {"offset": offset, "timeout": 30})
            if res.get("ok"):
                for update in res.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message")
                    if msg:
                        chat_id = msg.get("chat", {}).get("id")
                        text = msg.get("text", "")
                        if text.startswith("/start"):
                            send_message(chat_id, f"{PEM['hi']} <b>Welcome!</b> Bot is active.", reply_markup=getMainMenu())
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    # Start Flask server in a separate thread so Render port stays open
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start Bot polling
    process_updates()
