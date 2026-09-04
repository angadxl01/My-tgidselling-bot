import os
import sqlite3
import re
import asyncio
import time
import logging
import csv
import zipfile
import shutil
import html
from datetime import datetime

from telethon import TelegramClient, events, Button
from telethon.errors import (
    SessionPasswordNeededError, 
    MessageNotModifiedError,
    UserNotParticipantError,
    ChatAdminRequiredError
)
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.account import GetPasswordRequest

# ================= SAFE STYLED & CUSTOM EMOJI BUTTON WRAPPERS =================
_orig_btn_inline = Button.inline
_orig_btn_text = Button.text
_orig_btn_url = Button.url

def custom_text_button(text, *, resize=True, single_use=None, selective=None, style=None, icon_custom_emoji_id=None):
    try:
        if style or icon_custom_emoji_id:
            kwargs = {'resize': resize, 'single_use': single_use, 'selective': selective}
            if style: kwargs['style'] = style
            if icon_custom_emoji_id: kwargs['icon_custom_emoji_id'] = int(icon_custom_emoji_id)
            return _orig_btn_text(text, **kwargs)
    except (TypeError, Exception):
        pass
    btn = _orig_btn_text(text, resize=resize, single_use=single_use, selective=selective)
    if style:
        try: setattr(btn, 'style', style)
        except: pass
    if icon_custom_emoji_id:
        try: setattr(btn, 'icon_custom_emoji_id', int(icon_custom_emoji_id))
        except: pass
    return btn

def custom_inline_button(text, data=None, *, style=None, icon_custom_emoji_id=None):
    try:
        if style or icon_custom_emoji_id:
            kwargs = {}
            if style: kwargs['style'] = style
            if icon_custom_emoji_id: kwargs['icon_custom_emoji_id'] = int(icon_custom_emoji_id)
            return _orig_btn_inline(text, data, **kwargs)
    except (TypeError, Exception):
        pass
    btn = _orig_btn_inline(text, data)
    if style:
        try: setattr(btn, 'style', style)
        except: pass
    if icon_custom_emoji_id:
        try: setattr(btn, 'icon_custom_emoji_id', int(icon_custom_emoji_id))
        except: pass
    return btn

def custom_url_button(text, url, *, style=None, icon_custom_emoji_id=None):
    try:
        if style or icon_custom_emoji_id:
            kwargs = {}
            if style: kwargs['style'] = style
            if icon_custom_emoji_id: kwargs['icon_custom_emoji_id'] = int(icon_custom_emoji_id)
            return _orig_btn_url(text, url, **kwargs)
    except (TypeError, Exception):
        pass
    btn = _orig_btn_url(text, url)
    if style:
        try: setattr(btn, 'style', style)
        except: pass
    if icon_custom_emoji_id:
        try: setattr(btn, 'icon_custom_emoji_id', int(icon_custom_emoji_id))
        except: pass
    return btn

Button.text = custom_text_button
Button.inline = custom_inline_button
Button.url = custom_url_button

# ================= CONFIGURATION =================
API_ID = 36645562
API_HASH = "ccad405579d80b82492abbf4a7777907"
BOT_TOKEN = "8881219711:AAH5FwywIwDDx3GmT69wqEG_JTInWquzShk" 
ADMIN_ID = 8895089247

# CHANNELS
LOG_CHANNEL_ID = -1003940330621 
CHECK_CHANNELS = [-1003940330621, -1003468139933]
JOIN_URLS = [
    "https://t.me/+5ie3z_oE12UzYWE1",
    "https://t.me/+3R-sOuFv4mY5NmZl"
]

# LINKS & MEDIA
TERMS_URL = "https://tgtele.onrender.com/"

OTP_REGEX = r"\b\d{4,8}\b" 
AUTO_CANCEL_SECONDS = 600 

# ================= TELEGRAM CUSTOM TG-EMOJIS =================
P_YES = '<tg-emoji emoji-id="6267008582294705964">✅</tg-emoji>'
P_NO = '<tg-emoji emoji-id="5785177332595561481">❌</tg-emoji>'
P_PKG = '<tg-emoji emoji-id="6269214795325510848">📦</tg-emoji>'
P_MONEY = '<tg-emoji emoji-id="6267068789146260253">💰</tg-emoji>'
P_USDT = '<tg-emoji emoji-id="6030805455691846426">💵</tg-emoji>'
P_INR = '₹'
P_TG = '<tg-emoji emoji-id="6030595736733749484">✈️</tg-emoji>'
P_GIFT = '<tg-emoji emoji-id="6269214795325510848">🎁</tg-emoji>'
P_STATS = '<tg-emoji emoji-id="6033118016407868078">📊</tg-emoji>'
P_CARD = '<tg-emoji emoji-id="6028517788606272241">💳</tg-emoji>'
P_USERS = '<tg-emoji emoji-id="6034834452843074121">👥</tg-emoji>'
P_CAL = '<tg-emoji emoji-id="6266947228686892459">📅</tg-emoji>'
P_PC = '<tg-emoji emoji-id="6028461966916327262">💻</tg-emoji>'
P_EYE = '<tg-emoji emoji-id="5897520981135593826">👁️</tg-emoji>'
P_CW = '<tg-emoji emoji-id="6028517788606272241">👛</tg-emoji>'
P_ON = '<tg-emoji emoji-id="6032975852990370635">🟢</tg-emoji>'
P_OFF = '<tg-emoji emoji-id="6267262260243076354">🛑</tg-emoji>'
P_ID = '<tg-emoji emoji-id="5769547529993588669">👑</tg-emoji>'
P_KEY = '<tg-emoji emoji-id="6282846669335702032">⌨️</tg-emoji>'
P_GLOBE = '<tg-emoji emoji-id="6028126693179264852">🌐</tg-emoji>'
P_CART = '<tg-emoji emoji-id="5780824606579364273">🛒</tg-emoji>'
P_STORE = '<tg-emoji emoji-id="6028497653799588476">🏬</tg-emoji>'
P_OTP = '<tg-emoji emoji-id="6028102362189533369">🔢</tg-emoji>'
P_2FA = '<tg-emoji emoji-id="6282846669335702032">🔐</tg-emoji>'
P_FLAG = '<tg-emoji emoji-id="5967276872134824140">📍</tg-emoji>'
P_PHONE = '<tg-emoji emoji-id="6028500960924406167">📱</tg-emoji>'
P_WAIT = '<tg-emoji emoji-id="6267229004311303657">⏳</tg-emoji>'
P_TIME = '<tg-emoji emoji-id="6285240160120477644">⏰</tg-emoji>'
P_WARN = '<tg-emoji emoji-id="6267039884016358504">⚠️</tg-emoji>'
P_DOC = '<tg-emoji emoji-id="6264777724741556322">📃</tg-emoji>'
P_ASST = '<tg-emoji emoji-id="6267150926100829360">🤖</tg-emoji>'
P_ACC = '<tg-emoji emoji-id="6282567341842633593">👤</tg-emoji>'
P_FIRE = '<tg-emoji emoji-id="6264785189394717307">🔥</tg-emoji>'
P_STAR = '<tg-emoji emoji-id="6267118537752450044">🌟</tg-emoji>'
P_DIAMOND = '<tg-emoji emoji-id="5767137507879685567">💎</tg-emoji>'
P_BELL = '<tg-emoji emoji-id="5915814406490427591">🔔</tg-emoji>'
P_CROWN = '<tg-emoji emoji-id="5769547529993588669">👑</tg-emoji>'

# ================= INITIALIZATION =================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs("sessions", exist_ok=True)

session_name = f"bot_session_{BOT_TOKEN.split(':')[0]}"
bot = TelegramClient(session_name, API_ID, API_HASH)
bot.parse_mode = 'html'

db = sqlite3.connect("otp_bot_final.db", check_same_thread=False, timeout=20)
db.execute("PRAGMA journal_mode=WAL;")
cur = db.cursor()

active_orders = {}      
waiting_proof = {}      
deposit_input = {} 
admin_dep_state = {}    
user_spam_cooldown = {} 
session_buy_state = {}  
custom_dep_amt = {}     

user_locks = {}

def get_user_lock(uid):
    if uid not in user_locks:
        user_locks[uid] = asyncio.Lock()
    return user_locks[uid]

# ================= DATABASE SCHEMA =================
def setup_db():
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0,
        referred_by INTEGER,
        total_deposited INTEGER DEFAULT 0,
        joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        banned INTEGER DEFAULT 0,
        discount INTEGER DEFAULT 0,
        terms_accepted INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS stock (
        phone TEXT PRIMARY KEY,
        session_file TEXT,
        country_name TEXT,
        country_icon TEXT DEFAULT '',
        account_year INTEGER,
        category TEXT DEFAULT 'Good',
        price INTEGER,
        available INTEGER DEFAULT 1,
        twofa TEXT DEFAULT 'None',
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS auto_prices (
        country TEXT,
        year TEXT,
        price INTEGER,
        PRIMARY KEY (country, year)
    );
    CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        method_name TEXT,
        status TEXT, 
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        country TEXT,
        year INTEGER,
        price INTEGER,
        phone TEXT,
        otp TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS custom_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        caption TEXT,
        qr_file_id TEXT
    );
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        p_add_stock INTEGER DEFAULT 0,
        p_manage_stock INTEGER DEFAULT 0,
        p_stats INTEGER DEFAULT 0,
        p_bal INTEGER DEFAULT 0,
        p_settings INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS custom_countries (
        code TEXT PRIMARY KEY,
        name TEXT,
        flag TEXT DEFAULT ''
    );
    """)
    db.commit()

setup_db()

# ================= HELPER FUNCTIONS =================
def is_bot_online():
    res = cur.execute("SELECT value FROM settings WHERE key='bot_status'").fetchone()
    return res[0] == 'on' if res else True

def is_admin(uid):
    if uid == ADMIN_ID: return True
    row = cur.execute("SELECT user_id FROM admins WHERE user_id=?", (uid,)).fetchone()
    return bool(row)

def has_perm(uid, perm):
    if uid == ADMIN_ID: return True
    row = cur.execute(f"SELECT {perm} FROM admins WHERE user_id=?", (uid,)).fetchone()
    return bool(row and row[0] == 1)

def ensure_user(uid):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    db.commit()

def get_usdt_rate():
    res = cur.execute("SELECT value FROM settings WHERE key='usdt_rate'").fetchone()
    try: return float(res[0]) if res else 94.0
    except: return 94.0

def get_support_url():
    res = cur.execute("SELECT value FROM settings WHERE key='support_url'").fetchone()
    url = res[0] if res and res[0] else "https://t.me/tgtelehelpbot"
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://t.me/" + url.lstrip("@")
    return url

def get_support_channel_url():
    res = cur.execute("SELECT value FROM settings WHERE key='support_channel_url'").fetchone()
    url = res[0] if res and res[0] else JOIN_URLS[0]
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://t.me/" + url.lstrip("@")
    return url

def to_usd(inr):
    return round(inr / get_usdt_rate(), 2)

def is_user_banned(uid):
    res = cur.execute("SELECT banned FROM users WHERE user_id=?", (uid,)).fetchone()
    return res and res[0] == 1

def update_balance(uid, amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    db.commit()

def delete_session_files(session_path):
    base = session_path if not session_path.endswith('.session') else session_path[:-8]
    for ext in ['.session', '.session-wal', '.session-shm', '.session-journal']:
        try:
            if os.path.exists(base + ext): os.remove(base + ext)
        except: pass

async def check_channel_joined(uid):
    if is_admin(uid): return True
    for ch in CHECK_CHANNELS:
        try:
            channel = await bot.get_input_entity(ch)
            try:
                user = await bot.get_input_entity(uid)
            except Exception:
                user = await bot.get_entity(uid)
            await bot(GetParticipantRequest(channel=channel, participant=user))
        except (UserNotParticipantError, ValueError):
            return False
        except Exception as e:
            logger.error(f"Channel Check Error: {e}")
            return False
    return True

COUNTRY_CODES = {
    '1': 'USA/Canada', '7': 'Russia', '20': 'Egypt', '27': 'South Africa',
    '31': 'Netherlands', '32': 'Belgium', '33': 'France', '34': 'Spain',
    '39': 'Italy', '44': 'UK', '46': 'Sweden', '48': 'Poland',
    '49': 'Germany', '51': 'Peru', '52': 'Mexico', '54': 'Argentina',
    '55': 'Brazil', '56': 'Chile', '57': 'Colombia', '58': 'Venezuela',
    '60': 'Malaysia', '61': 'Australia', '62': 'Indonesia', '63': 'Philippines', 
    '66': 'Thailand', '84': 'Vietnam', '86': 'China', '90': 'Turkey',
    '91': 'India', '92': 'Pakistan', '93': 'Afghanistan', '94': 'Sri Lanka',
    '95': 'Myanmar', '98': 'Iran', '212': 'Morocco', '213': 'Algeria',
    '234': 'Nigeria', '254': 'Kenya', '255': 'Tanzania', '380': 'Ukraine',
    '880': 'Bangladesh', '964': 'Iraq', '966': 'Saudi Arabia', '971': 'UAE',
    '998': 'Uzbekistan'
}

def get_country_info(phone):
    phone = str(phone).replace(' ', '').replace('+', '')
    if not phone: return "Unknown"
    
    try:
        customs = cur.execute("SELECT code, name FROM custom_countries").fetchall()
        customs.sort(key=lambda x: len(x[0]), reverse=True)
        for code, name in customs:
            if phone.startswith(code): return name
    except: pass

    for length in (3, 2, 1):
        prefix = phone[:length]
        if prefix in COUNTRY_CODES: return COUNTRY_CODES[prefix]
    return "Unknown"

async def detect_account_year(client):
    year = 2024
    try:
        try: await client.delete_dialog('TGDNAbot')
        except: pass
        await client.send_message('TGDNAbot', '/start')
        me = await client.get_me()
        await asyncio.sleep(1)
        await client.send_message('TGDNAbot', str(me.id)) 
        for _ in range(8):
            await asyncio.sleep(1.5)
            msgs = await client.get_messages('TGDNAbot', limit=3)
            for m in msgs:
                if m.text and ('Created:' in m.text or 'Age:' in m.text or 'Registration' in m.text):
                    match = re.search(r'(?:Created|Age|Registration)[^\d]*(\d{4})', m.text, re.IGNORECASE)
                    if match: return int(match.group(1))
    except Exception: pass
    return year

# ================= LOGGING LOGIC =================
async def process_referral_bonus(uid, amount):
    row = cur.execute("SELECT referred_by FROM users WHERE user_id=?", (uid,)).fetchone()
    ref = row[0] if row else None
    if ref:
        pct_row = cur.execute("SELECT value FROM settings WHERE key='ref_percent'").fetchone()
        pct = float(pct_row[0]) if pct_row else 3.0
        if pct > 0:
            bonus = int(amount * (pct / 100))
            if bonus > 0:
                update_balance(ref, bonus)
                try: 
                    await bot.send_message(ref, f"{P_GIFT} <b>Referral Bonus!</b>\nYour referral <code>{uid}</code> deposited {P_INR}{amount}.\n{P_YES} You earned <b>{P_INR}{bonus}</b>!")
                except: pass

async def log_primary_deposit(uid, amt, method):
    try:
        try:
            user = await bot.get_entity(int(uid))
            username = html.escape(user.username) if user and user.username else "NoUsername"
        except:
            username = "NoUsername"
        t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        msg = (f"{P_YES} <b>NEW DEPOSIT SUCCESSFUL</b>\n\n"
               f"{P_ACC} User ID: <code>{uid}</code>\n"
               f"{P_ACC} Username: @{username}\n"
               f"{P_MONEY} Amount: {P_INR}{amt}\n"
               f"{P_CARD} Method: {html.escape(str(method))}\n"
               f"{P_TIME} Time: {t}\n\n"
               f"<i>{P_STAR} Thanks For Deposit In Fresh TG! {P_STAR}</i>")
        try: await bot.send_message(LOG_CHANNEL_ID, msg)
        except Exception as e: logger.error(f"Failed Log: {e}")
    except Exception as e: logger.error(f"Global Dep Log Err: {e}")

async def log_primary_purchase(uid, country, price, amount, year, qty):
    try:
        t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        country_clean = html.escape(str(country))
        msg = (f"{P_CART} <b>NEW PURCHASE SUCCESSFUL</b>\n\n"
               f"{P_ID} User ID: <code>{uid}</code>\n"
               f"{P_GLOBE} Country: {country_clean}\n"
               f"{P_MONEY} Price: {P_INR}{price}\n"
               f"{P_CARD} Total Paid: {P_INR}{amount}\n"
               f"{P_CAL} Year: {year}\n"
               f"{P_PKG} Quantity: {qty}\n"
               f"{P_TIME} Time: {t}")
        try: await bot.send_message(LOG_CHANNEL_ID, msg)
        except: pass
    except Exception as e: logger.error(f"Pur Log Err: {e}")

# ================= MENU HELPERS =================
def get_persistent_menu(uid):
    rows = [
        [Button.text("Buy Account", style="danger", icon_custom_emoji_id=5780824606579364273, resize=True)],
        [
            Button.text("Buy Sessions", style="success", icon_custom_emoji_id=6269214795325510848), 
            Button.text("Deposit", style="success", icon_custom_emoji_id=6267068789146260253)
        ],
        [
            Button.text("My Profile", style="primary", icon_custom_emoji_id=6282567341842633593), 
            Button.text("My Stats", style="primary", icon_custom_emoji_id=6033118016407868078)
        ],
        [Button.text("Support", style="success", icon_custom_emoji_id=6266794310671275367)]
    ]
    if is_admin(uid): 
        rows.append([Button.text("Admin Panel", style="danger", icon_custom_emoji_id=5769547529993588669)])
    return rows

async def send_main_menu(event, uid):
    me = await bot.get_me()
    pct_row = cur.execute("SELECT value FROM settings WHERE key='ref_percent'").fetchone()
    pct = pct_row[0] if pct_row else "3"
    msg = (f"{P_CROWN} <b>Welcome to TG ACC STORE!</b>\n\n"
           f"{P_GIFT} <b>Refer & Earn:</b>\nInvite friends and earn {pct}% of their deposits!\n"
           f"{P_GLOBE} <code>https://t.me/{me.username}?start=ref_{uid}</code>")
    
    if isinstance(event, events.CallbackQuery.Event):
        try: await event.delete()
        except: pass
        await bot.send_message(uid, msg, buttons=get_persistent_menu(uid))
    else:
        await event.respond(msg, buttons=get_persistent_menu(uid))

# ================= DEPOSIT HANDLERS =================
def format_payment_buttons(buttons):
    n = len(buttons)
    res = []
    for i in range(0, n, 2): res.append(buttons[i:i+2])
    return res

async def deposit_menu(event):
    msg = f"{P_CARD} <b>Select Payment Method:</b>\n\nChoose any payment method below to load funds."
    flat_buttons = []
    customs = cur.execute("SELECT name FROM custom_payments").fetchall()
    for c in customs:
        flat_buttons.append(Button.inline(f"{c[0]}", f"depm_{c[0]}", style="primary", icon_custom_emoji_id=6028517788606272241))
    
    if not flat_buttons:
        msg += f"\n\n{P_WARN} No active payment methods found at the moment."
    
    btns = format_payment_buttons(flat_buttons)
    await bot.send_message(event.chat_id, msg, buttons=btns)

def get_admin_custom_keypad(dep_id):
    return [
        [Button.inline("1", f"dkp|{dep_id}|1", style="primary"), Button.inline("2", f"dkp|{dep_id}|2", style="primary"), Button.inline("3", f"dkp|{dep_id}|3", style="primary")],
        [Button.inline("4", f"dkp|{dep_id}|4", style="primary"), Button.inline("5", f"dkp|{dep_id}|5", style="primary"), Button.inline("6", f"dkp|{dep_id}|6", style="primary")],
        [Button.inline("7", f"dkp|{dep_id}|7", style="primary"), Button.inline("8", f"dkp|{dep_id}|8", style="primary"), Button.inline("9", f"dkp|{dep_id}|9", style="primary")],
        [Button.inline("Del", f"dkp|{dep_id}|del", style="danger"), Button.inline("0", f"dkp|{dep_id}|0", style="primary"), Button.inline("Confirm", f"dkp|{dep_id}|conf", style="success", icon_custom_emoji_id=6267008582294705964)],
        [Button.inline("Cancel", f"dkp|{dep_id}|cancel", style="danger", icon_custom_emoji_id=5785177332595561481)]
    ]

async def manual_deposit_init(event, method):
    uid = event.sender_id
    deposit_input[uid] = {'step': 'wait_amt', 'method': method}
    await event.edit(f"{P_CARD} <b>{html.escape(method)} Deposit</b>\n\nReply to this message with the <b>AMOUNT</b> in INR (₹) you want to deposit.", buttons=[[Button.inline("Cancel", "cancel_action", style="danger", icon_custom_emoji_id=5785177332595561481)]])

# ================= BUYING FLOW =================
async def show_countries(event, flow, page=1):
    limit = 10
    offset = (page - 1) * limit
