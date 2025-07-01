from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import pytz
import os

from SchedulerAyah.send_daily_ayah import send_daily_random_ayah_to_all_users


def start_daily_ayah_scheduler(bot_token):
    bot = Bot(token=bot_token)

    scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Tashkent"))

    # Har kuni soat 09:00 da ishga tushadi
    scheduler.add_job(
        send_daily_random_ayah_to_all_users,
        trigger='cron',
        hour=1,
        minute=41,
        args=[bot],
        id="daily_ayah_job",
        replace_existing=True
    )

    scheduler.start()
