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
        [InlineKeyboardButton("🏆 Reytingni ko'rish", callback_data="ramadan_leaderboard")],
        [InlineKeyboardButton("📍 Hududni tanlash", callback_data="ramadan_set_region")],
        [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="ramadan_insta_verify")]
    ]
    update.message.reply_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def leaderboard_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    text = get_leaderboard_text()
    keyboard = [[InlineKeyboardButton("⬅️ Orqaga", callback_data="ramadan_back_to_status")]]
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
        [InlineKeyboardButton("🏆 Reytingni ko'rish", callback_data="ramadan_leaderboard")],
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
        [InlineKeyboardButton("🏆 Reytingni ko'rish", callback_data="ramadan_leaderboard")],
        [InlineKeyboardButton("📍 Hududni tanlash", callback_data="ramadan_set_region")],
        [InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="ramadan_insta_verify")]
    ]
    if query:
        query.edit_message_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(status_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def juma_test_command(update: Update, context: CallbackContext):
    from Ramadan.quiz_integration import start_friday_quiz
    from datetime import datetime
    
    # Check if today is Friday (4 is Friday)
    if datetime.now().weekday() != 4:
        # Per user request, we allow testing (mocking Friday)
        # But for production it should be strict.
        pass 

    start_friday_quiz(update, context)
