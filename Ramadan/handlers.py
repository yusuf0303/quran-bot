from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from Ramadan.database import register_contest_user, get_contest_user, add_points, verify_referral
from Ramadan.contest_logic import get_konkurs_status, get_leaderboard_text, check_subscription, INSTAGRAM_URL
from Ramadan.hududlar import REGIONS
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ramadan.db")

def konkurs_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    full_name = update.effective_user.full_name
    
    register_contest_user(user_id, full_name)
    
    # Check if user already got self-join bonus
    user = get_contest_user(user_id)
    if user and user[5] == 0: # has_joined_bonus
        if check_subscription(context.bot, user_id):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE contest_users SET points = points + 5, has_joined_bonus = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            update.message.reply_text("🎊 Tabriklaymiz! Obuna bo'lganingiz uchun 5 ball berildi.")
            
            # Verify if this user was a referral
            referrer_id = verify_referral(user_id)
            if referrer_id:
                try:
                    context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎊 Do'stingiz {full_name} botga qo'shildi va kanalga a'zo bo'ldi! Sizga 10 ball taqdim etildi."
                    )
                except Exception:
                    pass

    status_text = get_konkurs_status(user_id, context.bot.username)
    
    keyboard = [
        [InlineKeyboardButton("📸 Instagram", url=INSTAGRAM_URL),
        InlineKeyboardButton("📢 Telegram kanal", url="https://t.me/KalomUz_News")],
        [InlineKeyboardButton("👥 Do'stlarni taklif qilish", switch_inline_query=f"ramadan_r{user_id}")],
        [InlineKeyboardButton("🏆 Reytingni ko'rish", callback_data="ramadan_leaderboard"),
         InlineKeyboardButton("🌙 Juma Testi 🚀", callback_data="start_friday_test")],
        [InlineKeyboardButton("📍 Hududni tanlash", callback_data="ramadan_set_region")],
        [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="ramadan_insta_verify")]
    ]
    update.message.reply_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def leaderboard_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    # Extract page from data: ramadan_leaderboard_PAGE
    data = query.data
    page = 1
    if "_" in data and data.split("_")[-1].isdigit():
        page = int(data.split("_")[-1])
    
    from Ramadan.database import get_total_contest_users
    total = get_total_contest_users()
    limit = 10
    total_pages = (total + limit - 1) // limit
    
    text = get_leaderboard_text(page=page, limit=limit, total=total)
    
    keyboard = []
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"ramadan_leaderboard_{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"ramadan_leaderboard_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
        
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="ramadan_back_to_status")])
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def set_region_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()
    
    keyboard = []
    row = []
    for region in REGIONS.keys():
        row.append(InlineKeyboardButton(region, callback_data=f"ramadan_save_reg_{region}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="ramadan_back_to_status")])
    text = "📍 Iltimos, o'zingiz yashaydigan hududni tanlang:"
    if query:
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def save_region_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    region = query.data.replace("ramadan_save_reg_", "")
    user_id = update.effective_user.id
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE contest_users SET region = ? WHERE user_id = ?", (region, user_id))
    conn.commit()
    conn.close()
    
    query.answer(f"✅ Hudud {region} ga o'zgartirildi!")
    
    # Show status again
    status_text = get_konkurs_status(user_id, context.bot.username)
    keyboard = [
        [InlineKeyboardButton("📸 Instagram", url=INSTAGRAM_URL),
        InlineKeyboardButton("📢 Telegram kanal", url="https://t.me/KalomUz_News")],
        [InlineKeyboardButton("👥 Do'stlarni taklif qilish", switch_inline_query=f"ramadan_r{user_id}")],
        [InlineKeyboardButton("🏆 Reytingni ko'rish", callback_data="ramadan_leaderboard"),
         InlineKeyboardButton("🌙 Juma Testi 🚀", callback_data="start_friday_test")],
        [InlineKeyboardButton("📍 Hududni tanlash", callback_data="ramadan_set_region")],
        [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="ramadan_insta_verify")]
    ]
    query.edit_message_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def insta_verify_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE contest_users SET instagram_claimed = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    query.answer("✅ Instagramga obuna bo'lganingiz qayd etildi! G'olib bo'lsangiz, bu qo'shimcha tekshiriladi.", show_alert=True)

def ramadan_back_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()
    user_id = update.effective_user.id
    status_text = get_konkurs_status(user_id, context.bot.username)
    
    keyboard = [
        [InlineKeyboardButton("📸 Instagram", url=INSTAGRAM_URL),
        InlineKeyboardButton("📢 Telegram kanal", url="https://t.me/KalomUz_News")],
        [InlineKeyboardButton("👥 Do'stlarni taklif qilish", switch_inline_query=f"ramadan_r{user_id}")],
        [InlineKeyboardButton("🏆 Reytingni ko'rish", callback_data="ramadan_leaderboard"),
         InlineKeyboardButton("🌙 Juma Testi 🚀", callback_data="start_friday_test")],
        [InlineKeyboardButton("📍 Hududni tanlash", callback_data="ramadan_set_region")],
        [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="ramadan_insta_verify")]
    ]
    if query:
        query.edit_message_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def juma_test_command(update: Update, context: CallbackContext):
    from Ramadan.quiz_integration import send_friday_quiz_notification
    from datetime import datetime
    
    now = datetime.now()
    # Debugging: Allow Friday (4)
    if now.weekday() not in [4]:
        update.message.reply_text("⚠️ **Bugun juma emas!**\n\nJuma testi faqat juma kunlari bo'lib o'tadi. Iltimos, juma kunini kuting!", parse_mode=ParseMode.MARKDOWN)
        return

    send_friday_quiz_notification(update, context)
