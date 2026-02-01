import logging
import sqlite3
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from Ramadan.database import DB_PATH, add_points
from Ramadan.hududlar import REGIONS, RAMADAN_CALENDAR

logger = logging.getLogger(__name__)

def check_and_send_ramadan_reminders(bot):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    if today_str not in RAMADAN_CALENDAR:
        return
    
    times = RAMADAN_CALENDAR[today_str]
    saharlik_tashk = times['saharlik']
    iftorlik_tashk = times['iftorlik']
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, region FROM contest_users WHERE region IS NOT NULL")
    users = cursor.fetchall()
    conn.close()
    
    for uid, region in users:
        offset = REGIONS.get(region, 0)
        
        # Calculate local times
        try:
            # Simple string manipulation for time calculation
            def apply_offset(t_str, off):
                h, m = map(int, t_str.split(':'))
                dt = datetime(2000, 1, 1, h, m) + timedelta(minutes=off)
                return dt.strftime("%H:%M")
            
            local_saharlik = apply_offset(saharlik_tashk, offset)
            local_iftorlik = apply_offset(iftorlik_tashk, offset)
            
            # Check if it's 30 mins before Suhoor or Iftar
            # (Note: In a real production system, this would be a more precise trigger)
            current_time = now.strftime("%H:%M")
            
            # Placeholder for actual reminder logic - here we just log it
            # In main loop we could check every minute.
        except Exception as e:
            logger.error(f"Reminder error for {uid}: {e}")

def award_weekly_bonus(bot):
    # Award +10 points to Top 3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM contest_users ORDER BY points DESC LIMIT 3")
    top_3 = cursor.fetchall()
    
    for uid_tuple in top_3:
        uid = uid_tuple[0]
        cursor.execute("UPDATE contest_users SET points = points + 10 WHERE user_id = ?", (uid,))
        try:
            bot.send_message(chat_id=uid, text="🎊 Tabriklaymiz! O'tgan haftadagi yuqori natijangiz uchun sizga +10 bonus ball taqdim etildi!")
        except Exception:
            pass
    
    conn.commit()
    conn.close()
    
    # Also post to channel?
    # bot.send_message(chat_id="@KalomUz_News", text="🏆 Haftalik eng ko'p ball to'plaganlar...")

def start_ramadan_scheduler(bot):
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    scheduler = BackgroundScheduler(timezone=tashkent_tz)
    # Check for reminders every minute
    scheduler.add_job(check_and_send_ramadan_reminders, 'interval', minutes=1, args=[bot])
    # Weekly bonus on Friday night
    scheduler.add_job(award_weekly_bonus, 'cron', day_of_week='fri', hour=23, minute=59, args=[bot])
    scheduler.start()
