#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==========================================
# Install requirements before running:
# pip install requests pyotp
# ==========================================
import requests
import time
import json
import os
import pyotp
import uuid
import csv

# ==========================================
# Configuration (Aapki details set hain)
# ==========================================
TOKEN = "8510543770:AAEHSpib5zdObv1F1MLKReQhVmrkERTlKFE"
ADMIN_ID = 8438207365
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
DB_FILE = "database.json"
tg_session = requests.Session()

# Premium Emojis
PEM = {
  "ok": '<tg-emoji emoji-id="6111726981760423576">✅</tg-emoji>',
  "no": '<tg-emoji emoji-id="6311965254817423602">❌</tg-emoji>',
  "warn": '<tg-emoji emoji-id="6314510813214284503">⚠️</tg-emoji>',
  "admin": '<tg-emoji emoji-id="5353032893096567467">📊</tg-emoji>',
  "user": '<tg-emoji emoji-id="5352861489541714456">👤</tg-emoji>',
  "money": '<tg-emoji emoji-id="6111799373434197692">💸</tg-emoji>',
  "gift": '<tg-emoji emoji-id="6109561463544747928">🎁</tg-emoji>',
  "msg": '<tg-emoji emoji-id="5337302974806922068">💬</tg-emoji>',
  "cookie": '<tg-emoji emoji-id="6314402846326397461">🍪</tg-emoji>',
  "rocket": '<tg-emoji emoji-id="5352597830089347330">🚀</tg-emoji>',
  "target": '<tg-emoji emoji-id="6109432142079466939">🎯</tg-emoji>',
  "pin": '<tg-emoji emoji-id="6111410240807245099">📌</tg-emoji>',
  "hi": '<tg-emoji emoji-id="5353027129250453493">👋</tg-emoji>',
  "add": '<tg-emoji emoji-id="6188038822509418008">➕</tg-emoji>',
  "rem": '<tg-emoji emoji-id="6188343249791358585">➖</tg-emoji>',
  "view": '<tg-emoji emoji-id="6188447235244562676">👀</tg-emoji>',
  "key": '<tg-emoji emoji-id="6233302765582424442">🔑</tg-emoji>',
  "wait": '<tg-emoji emoji-id="6233136657722251031">⏳</tg-emoji>',
  "earn": '<tg-emoji emoji-id="6186175669991379791">🤑</tg-emoji>',
  "bell": '<tg-emoji emoji-id="6260082445018731350">🔔</tg-emoji>',
  "crown": '<tg-emoji emoji-id="6183661284467152997">👑</tg-emoji>',
  "gear": '<tg-emoji emoji-id="6260111633616475361">⚙️</tg-emoji>',
  "group": '<tg-emoji emoji-id="6233527959307688784">👥</tg-emoji>',
  "check": '<tg-emoji emoji-id="6188038822509418008">✅</tg-emoji>',
  "join": '<tg-emoji emoji-id="5352597830089347330">➡️</tg-emoji>'
}

# Databases
users = {}
submissions = []
rates = {"ig_2fa": 3.00, "fb_cookies": 4.50}
admin_settings = {
    "supportUrl": "https://t.me/EasyIncomeX_Support",
    "withdrawMethods": [{"name": "bKash", "minAmount": 50}, {"name": "Nagad", "minAmount": 50}],
    "newUserGuide": {"type": "text", "text": "কীভাবে কাজ করবেন তা জানতে আমাদের গাইড পড়ুন।"},
    "igGuide": {"type": "text", "text": "Instagram এর কাজ করার নিয়ম এখানে থাকবে।"},
    "fbGuide": {"type": "text", "text": "Facebook এর কাজ করার নিয়ম এখানে থাকবে।"},
    "referralTasksRequired": 5,
    "referralBonusAmount": 10.0
}
bot_username = "EasyIncomeX_bot"
user_states = {}
user_current_task = {}
user_temp_data = {}

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
                if "referralTasksRequired" not in admin_settings:
                    admin_settings["referralTasksRequired"] = 5
                if "referralBonusAmount" not in admin_settings:
                    admin_settings["referralBonusAmount"] = 10.0
                if "admins" not in admin_settings:
                    admin_settings["admins"] = []
                if "must_join_channel" not in admin_settings:
                    admin_settings["must_join_channel"] = ""
                if "igGuide" not in admin_settings:
                    admin_settings["igGuide"] = {"type": "text", "text": "Instagram এর কাজ করার নিয়ম এখানে থাকবে।"}
                if "fbGuide" not in admin_settings:
                    admin_settings["fbGuide"] = {"type": "text", "text": "Facebook এর কাজ করার নিয়ম এখানে থাকবে।"}
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

def check_force_sub(chat_id):
    channel = admin_settings.get("must_join_channel", "")
    if not channel:
        return True
    res = api_call("getChatMember", {"chat_id": channel, "user_id": chat_id})
    if not res.get("ok"):
        return False
    status = res["result"].get("status")
    return status in ["member", "administrator", "creator"]

def ask_force_sub(chat_id):
    channel = admin_settings.get("must_join_channel", "")
    kb = [
        [{"text": "Join Channel", "url": f"https://t.me/{channel.replace('@', '')}", "icon_custom_emoji_id": "5352597830089347330", "style": "primary"}],
        [{"text": "Joined", "callback_data": "check_sub", "icon_custom_emoji_id": "6188038822509418008", "style": "success"}]
    ]
    send_message(chat_id, f"{PEM['warn']} <b>Must Join Channel!</b>\nYou must join our channel to use this bot.", reply_markup={"inline_keyboard": kb})

def init_user(chat_id, username, first_name, referrer_id=None):
    if chat_id not in users:
        ref = None
        if referrer_id and referrer_id.isdigit():
            ref_int = int(referrer_id)
            if ref_int != chat_id:
                ref = ref_int
        users[chat_id] = {
            "id": chat_id,
            "username": username,
            "first_name": first_name,
            "balance": 0.0,
            "totalEarned": 0.0,
            "joinedAt": time.time(),
            "referredBy": ref,
            "referralBonusPaid": False
        }
        save_db()
    else:
        updated = False
        if users[chat_id].get("username") != username:
            users[chat_id]["username"] = username
            updated = True
        if users[chat_id].get("first_name") != first_name:
            users[chat_id]["first_name"] = first_name
            updated = True
        if updated:
            save_db()

# --- API Methods ---
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

def download_file(file_id, save_path):
    res = api_call("getFile", {"file_id": file_id})
    if res.get("ok"):
        file_path = res["result"].get("file_path")
        url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        try:
            r = tg_session.get(url, timeout=60)
            if r.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(r.content)
                return True
        except Exception:
            pass
    return False

# --- Keyboards ---
def getMainMenu():
    return {
        "keyboard": [
            [
                {"text": "Work", "icon_custom_emoji_id": "6111410240807245099", "style": "primary"}, 
                {"text": "Balance", "icon_custom_emoji_id": "6111799373434197692", "style": "success"}
            ],
            [
                {"text": "Withdraw", "icon_custom_emoji_id": "6111799373434197692", "style": "primary"}, 
                {"text": "My Referrals", "icon_custom_emoji_id": "6109561463544747928", "style": "success"}
            ],
            [
                {"text": "Support", "icon_custom_emoji_id": "5337302974806922068", "style": "primary"}, 
                {"text": "New User", "icon_custom_emoji_id": "5352861489541714456", "style": "primary"}
            ]
        ],
        "resize_keyboard": True
    }

def getAdminMenu(chat_id):
    kb = [
        [{"text": "Users List", "icon_custom_emoji_id": "5352861489541714456", "callback_data": "admin_users", "style": "primary"}, 
          {"text": "Broadcast", "icon_custom_emoji_id": "5337302974806922068", "callback_data": "admin_broadcast", "style": "success"}],
        [{"text": "Download DB", "icon_custom_emoji_id": "5352721946054268944", "callback_data": "admin_download_db", "style": "primary"}, 
         {"text": "Upload DB", "icon_custom_emoji_id": "5352721946054268944", "callback_data": "admin_upload_db", "style": "primary"}]
    ]
    return {"inline_keyboard": kb}

def handle_message(msg):
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id: return
    text = msg.get("text", "")
    username = msg.get("from", {}).get("username", "")
    first_name = msg.get("from", {}).get("first_name", "")
    
    init_user(chat_id, username, first_name)
    state = user_states.get(chat_id, "main")
    
    if text.startswith("/start"):
        user_states[chat_id] = "main"
        if not check_force_sub(chat_id):
            ask_force_sub(chat_id)
            return
        send_message(chat_id, f"{PEM['hi']} <b>Welcome to Bot!</b>\nSelect an option from the menu:", reply_markup=getMainMenu())
        return

    if text == "/admin":
        if is_admin(chat_id):
            send_message(chat_id, f"{PEM['admin']} <b>Admin Panel</b>", reply_markup=getAdminMenu(chat_id))
        return

    # Fix applied for state handling at the bottom:
    if state == "admin_awaiting_db":
        if "document" in msg:
            file_id = msg["document"]["file_id"]
            if download_file(file_id, DB_FILE):
                load_db()
                send_message(chat_id, f"{PEM['ok']} Database uploaded successfully.", reply_markup=getAdminMenu(chat_id))
            else:
                send_message(chat_id, f"{PEM['no']} Failed to download database.", reply_markup=getAdminMenu(chat_id))
        else:
            send_message(chat_id, f"{PEM['no']} Please send a valid database JSON file.", reply_markup=getAdminMenu(chat_id))
        user_states[chat_id] = "main"
        return
