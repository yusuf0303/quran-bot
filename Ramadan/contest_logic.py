from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from Ramadan.database import (
    register_contest_user, get_contest_user, add_points, 
    verify_referral, get_leaderboard, get_leaderboard_page, get_total_contest_users
)
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

def escape_markdown(text):
    """Helper to escape markdown special characters."""
    if not text: return ""
    return text.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")

def get_konkurs_status(user_id, bot_username):
    user = get_contest_user(user_id)
    if not user:
        return "Siz hali konkursda ro'yxatdan o'tmagansiz. /start ni bosing."
    
    uid, name, points, region, ref_count, joined_bonus, insta_claimed, last_quiz = user
    
    # Escape name to prevent markdown errors
    safe_name = escape_markdown(name)
    
    ref_link = f"https://t.me/{bot_username}?start=r{user_id}"
    
    status_text = (
        f"🌙 **Ramazon Konkursi 2026**\n\n"
        f"👤 **Foydalanuvchi:** {safe_name}\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"📍 **Hudud:** {region if region else 'Tanlanmagan /hudud'}\n\n"
        f"💰 **Jami ball:** {points}\n"
        f"👥 **Taklif qilingan do'stlar:** {ref_count} ta\n\n"
        f"🔗 **Sizning referal havolangiz:**\n`{ref_link}`\n\n"
        f"📜 **Shartlar:**\n"
        f"1. [KalomUz\\_News](https://t.me/KalomUz_News) kanaliga a'zo bo'lish (+5 ball)\n"
        f"2. [Instagram](https://instagram.com/kalomuz)ga obuna bo'lish (+5 ball)\n"
        f"3. Do'stlarni taklif qilish (Har bir do'st uchun +10 ball)\n"
        f"4. Juma kungi quiz testi (Har bir to'g'ri javob +5 ball)\n"
        f"5. Kundalik quizlar (Har bir to'g'ri javob +1 ball)\n\n"
        f"🎁 **Sovrinlar:** Eng ko'p ball to'plagan 3 kishiga kitoblar to'plami!"
    )
    return status_text

def get_leaderboard_text(page=1, limit=10, total=0):
    offset = (page - 1) * limit
    leaders = get_leaderboard_page(limit, offset)
    
    if not leaders:
        return "🏆 **Reyting jadvali hali bo'sh.**\nBallar yig'ishni hoziroq boshlang!"
    
    text = f"🏆 **Ramazon Konkursi - Reyting:**\n"
    text += f"📊 Jami ishtirokchilar: {total} ta\n\n"
    
    for i, (name, points) in enumerate(leaders, offset + 1):
        safe_name = escape_markdown(name)
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "👤"
        text += f"{i}. {medal} **{safe_name}** — {points} ball\n"
    
    text += f"\n📄 Sahifa: {page} / {(total + limit - 1) // limit}"
    text += "\n\nOlg'a! Siz ham g'olib bo'lishingiz mumkin! 🚀"
    return text
