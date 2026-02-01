from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from Ramadan.database import register_contest_user, get_contest_user, add_points, verify_referral, get_leaderboard
from Ramadan.hududlar import REGIONS

# Kanallar ro'yxati (Konkursda qatnashish uchun majburiy)
CHANNELS = ["@KalomUz_News"]
INSTAGRAM_URL = "https://instagram.com/kalomuz"

def check_subscription(bot, user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

def get_konkurs_status(user_id, bot_username):
    user = get_contest_user(user_id)
    if not user:
        return "Siz hali konkursda ro'yxatdan o'tmagansiz. /start ni bosing."
    
    uid, name, points, region, ref_count, joined_bonus, insta_claimed, last_quiz = user
    
    ref_link = f"https://t.me/{bot_username}?start=r{user_id}"
    
    status_text = (
        f"🌙 **Ramazon Konkursi 2026**\n\n"
        f"👤 **Foydalanuvchi:** {name}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"📍 **Hudud:** {region if region else 'Tanlanmagan /hudud'}\n\n"
        f"💰 **Jami ball:** {points}\n"
        f"👥 **Taklif qilingan do'stlar:** {ref_count} ta\n\n"
        f"🔗 **Sizning referal havolangiz:**\n{ref_link}\n\n"
        f"📜 **Shartlar:**\n"
        f"1. Botga va @KalomUz_News kanaliga a'zo bo'lish (+5 ball)\n"
        f"2. Instagramga obuna bo'lish ([Instagram]({INSTAGRAM_URL}))\n"
        f"3. Do'stlarni taklif qilish (Har bir do'st uchun +10 ball)\n"
        f"4. Juma kungi quiz testi (Har bir to'g'ri javob +5 ball)\n"
        f"5. Kundalik quizlar (Har bir to'g'ri javob +1 ball)\n\n"
        f"🎁 **Sovrinlar:** Eng ko'p ball to'plagan 3 kishiga kitoblar to'plami!"
    )
    return status_text

def get_leaderboard_text():
    leaders = get_leaderboard(10)
    if not leaders:
        return "🏆 **Reyting jadvali hali bo'sh.**\nBallar yig'ishni hoziroq boshlang!"
    
    text = "🏆 **Ramazon Konkursi - Kuchli 10 talik:**\n\n"
    for i, (name, points) in enumerate(leaders, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
        text += f"{i}. {medal} **{name}** — {points} ball\n"
    
    text += "\nOlg'a! Siz ham g'olib bo'lishingiz mumkin! 🚀"
    return text
