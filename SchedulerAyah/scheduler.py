import random
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import pytz
import logging
from datetime import datetime
from SchedulerAyah.send_daily_ayah import send_daily_random_ayah_to_all_users


def start_daily_ayah_scheduler(bot_token):
    bot = Bot(token=bot_token)
    scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Tashkent"))
    logging.basicConfig(level=logging.INFO)

    def schedule_random_job():
        now = datetime.now(pytz.timezone("Asia/Tashkent")).time()

        # Soat 00:00 da ishga tushganda
        if 0 <= now.hour < 1:
            start_hour, end_hour = 6, 12  # 06:00 - 12:59 oralig'i
        else:
            # Soat 13:00 da ishga tushganda
            start_hour, end_hour = 13, 20  # 13:01 - 20:00 oralig'i

        # Random soat va daqiqa tanlash
        random_hour = random.randint(start_hour, end_hour)
        random_minute = random.randint(0, 59)

        logging.info(f"📅  Yangi random vaqt tanlandi: {random_hour:02d}:{random_minute:02d}")

        # Eski 'daily_ayah_job' mavjud bo‘lsa — o‘chirib tashlaymiz
        try:
            scheduler.remove_job('daily_ayah_job')
        except:
            pass

        # Yangi random vaqtga job qo‘shamiz
        scheduler.add_job(
            send_daily_random_ayah_to_all_users,
            trigger='cron',
            hour=random_hour,
            minute=random_minute,
            args=[bot],
            id='daily_ayah_job',
            replace_existing=True
        )

        logging.info(f"🕒  Yangi job belgilandi: {random_hour:02d}:{random_minute:02d} da ishga tushadi")

    # Dastlab ishga tushganda bir random vaqt o‘rnatiladi
    schedule_random_job()

    # Har kuni 00:00 va 13:00 da yangi random vaqt tanlash
    scheduler.add_job(
        schedule_random_job,
        trigger='cron',
        hour='0,13',
        minute=0,
        id='rescheduler_job',
        replace_existing=True
    )

    scheduler.start()
    logging.info("✅ Scheduler ishga tushdi (00:00 va 13:00 da random vaqt tanlaydi)")
    return scheduler

