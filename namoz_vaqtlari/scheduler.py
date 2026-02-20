
import logging
import sqlite3
import os
import requests
import time
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from namoz_vaqtlari.get_regeions import API_REGION_NAMES
from namoz_vaqtlari.time_namoz import get_data, SAHARLIK_DUO, IFTORLIK_DUO

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Ramadan", "ramadan.db")

# Cache to store prayer times for all regions
# Structure: { "RegionName": { "tong_saharlik": "05:00", ... } }
prayer_cache = {}

def fetch_all_prayer_times():
    """Fetch and cache prayer times for all regions from islomapi.uz"""
    global prayer_cache
    new_cache = {}
    logger.info("Fetching prayer times for all regions...")
    for display_name, api_name in API_REGION_NAMES.items():
        try:
            # Use the robust get_data from time_namoz which has fallbacks
            data = get_data(display_name)
            if data and 'times' in data:
                new_cache[display_name] = data['times']
            else:
                logger.error(f"Failed to fetch prayer times for {display_name} even with fallbacks")
        except Exception as e:
            logger.error(f"Error fetching prayer times for {display_name}: {e}")
    
    if new_cache:
        prayer_cache = new_cache
        logger.info(f"Prayer times cached for {len(prayer_cache)} regions: {list(prayer_cache.keys())}")
    else:
        logger.error("DANGER: Prayer cache is empty after fetch!")

def check_and_send_prayer_reminders(bot):
    """Check every minute if any prayer is in 15 minutes and send reminders"""
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tashkent_tz)
    target_time = (now + timedelta(minutes=15)).strftime("%H:%M")
    
    # Prayer keys to check
    prayer_keys = {
        "tong_saharlik": "Bomdod (Saharlik)",
        "peshin": "Peshin",
        "asr": "Asr",
        "shom_iftor": "Shom (Iftor)",
        "hufton": "Xufton"
    }
    
    if not prayer_cache:
        fetch_all_prayer_times()
        if not prayer_cache: return

    # 1. Group regions by which prayer is happening in 15 mins
    reminders_to_send = {} # { "PrayerName": [region1, region2, ...] }
    
    for region, times in prayer_cache.items():
        for key, name in prayer_keys.items():
            if times.get(key) == target_time:
                if name not in reminders_to_send:
                    reminders_to_send[name] = []
                reminders_to_send[name].append(region)

    if not reminders_to_send:
        return

    logger.info(f"Sending prayer reminders for: {list(reminders_to_send.keys())}")

    # 2. Fetch users and their regions
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, region FROM contest_users")
        users = cursor.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Database error in scheduler: {e}")
        return

    # 3. Send reminders
    count = 0
    for user_id, user_region in users:
        # Default to Toshkent if no region selected
        region_to_check = user_region if user_region else "Toshkent"
        
        # In case the user_region is not in our display_name keys (e.g. "Nukus")
        if region_to_check == "Nukus": region_to_check = "Nukus (Qoraqalpog'iston Res)"
        
        for prayer_name, regions in reminders_to_send.items():
            if region_to_check in regions:
                try:
                    text = f"⏳ <b>{prayer_name}</b> vaqtiga 15 daqiqa qoldi.\n📍 Hudud: <b>{region_to_check}</b>"
                    
                    # Add Suhoor/Iftar prayers during Ramazan
                    if prayer_name == "Bomdod (Saharlik)":
                        text += f"\n\n{SAHARLIK_DUO}"
                    elif prayer_name == "Shom (Iftor)":
                        text += f"\n\n{IFTORLIK_DUO}"

                    keyboard = None
                    if not user_region:
                        text += "\n\n⚠️ Siz hali hudud tanlamagansiz, shuning uchun Toshkent vaqti ko'rsatilmoqda. Hududni tanlash uchun pastdagi tugmani bosing."
                        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("📍 Hududni tanlash", callback_data="ramadan_set_region")]])
                    
                    bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
                    count += 1
                    if count % 20 == 0: time.sleep(0.1) # Basic rate limiting
                except Exception:
                    # Likely bot blocked by user
                    pass

def start_prayer_scheduler(bot):
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    scheduler = BackgroundScheduler(timezone=tashkent_tz)
    
    # 1. Fetch times immediately on start
    fetch_all_prayer_times()
    
    # 2. Fetch times daily at 00:01
    scheduler.add_job(fetch_all_prayer_times, 'cron', hour=0, minute=1)
    
    # 3. Check for reminders every minute
    scheduler.add_job(check_and_send_prayer_reminders, 'interval', minutes=1, args=[bot])
    
    scheduler.start()
    logger.info("Prayer reminder scheduler started")
