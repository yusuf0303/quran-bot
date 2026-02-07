
import sqlite3
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.utils.helpers import escape_markdown
from telegram.ext import CallbackContext
import html

# Database paths
RAMADAN_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Ramadan", "ramadan.db")
QURAN_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Suralarni_toping", "ayah_game.db")

def get_stats_data():
    conn = sqlite3.connect(QURAN_DB)
    cursor = conn.cursor()
    
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    week_ago_str = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    month_ago_str = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    
    stats = {}
    
    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")
    stats['total'] = cursor.fetchone()[0]
    
    # Today
    cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at >= ?", (today_str + " 00:00:00",))
    stats['today'] = cursor.fetchone()[0]
    
    # Yesterday
    cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at >= ? AND registered_at < ?", 
                   (yesterday_str + " 00:00:00", today_str + " 00:00:00"))
    stats['yesterday'] = cursor.fetchone()[0]
    
    # Last Week
    cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at >= ?", (week_ago_str + " 00:00:00",))
    stats['week'] = cursor.fetchone()[0]
    
    # Last Month
    cursor.execute("SELECT COUNT(*) FROM users WHERE registered_at >= ?", (month_ago_str + " 00:00:00",))
    stats['month'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def get_region_stats():
    conn = sqlite3.connect(RAMADAN_DB)
    cursor = conn.cursor()
    
    # Count users by region
    cursor.execute("""
        SELECT region, COUNT(*) as count 
        FROM contest_users 
        GROUP BY region 
        ORDER BY count DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    region_stats = []
    for region, count in rows:
        region_name = region if region else "Tanlanmagan ❓"
        region_stats.append((region_name, count))
    
    return region_stats

def admin_stats_command(update: Update, context: CallbackContext):
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if update.effective_user.id != admin_id:
        return
        
    stats = get_stats_data()
    
    text = (
        "📊 <b>Bot Statistikasi</b>\n\n"
        f"👥 Jami obunachilar: <code>{stats['total']}</code>\n\n"
        f"📅 Bugun qo'shilgan: <code>{stats['today']}</code>\n"
        f"📆 Kecha qo'shilgan: <code>{stats['yesterday']}</code>\n"
        f"🗓 Oxirgi haftada: <code>{stats['week']}</code>\n"
        f"📅 Oxirgi oyda: <code>{stats['month']}</code>\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("👥 Foydalanuvchilar ro'yxati", callback_data="admin_users_1")],
        [InlineKeyboardButton("🗺 Hududlar bo'yicha", callback_data="admin_region_stats")]
    ]
    
    if update.callback_query:
        update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

def admin_users_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if update.effective_user.id != admin_id:
        if query: query.answer("Ruxsat berilmagan")
        return
    
    if query: query.answer()
    
    page = 1
    if query and query.data.startswith("admin_users_"):
        page = int(query.data.split("_")[-1])
        
    limit = 10
    offset = (page - 1) * limit
    
    conn = sqlite3.connect(QURAN_DB)
    cursor = conn.cursor()
    
    # Attach Ramadan DB to join with referrals
    cursor.execute(f"ATTACH DATABASE '{RAMADAN_DB}' AS ramadan")
    
    # Fetch users with their referrer info if available
    query_str = """
        SELECT 
            u.user_id, u.first_name, u.username, u.registered_at,
            r.referrer_id, ref.full_name as referrer_name
        FROM users u
        LEFT JOIN ramadan.referrals r ON u.user_id = r.referred_id
        LEFT JOIN ramadan.contest_users ref ON r.referrer_id = ref.user_id
        ORDER BY u.registered_at DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(query_str, (limit, offset))
    users = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    total_pages = max(1, (total_users + limit - 1) // limit)
    
    conn.close()
    
    text = f"👥 <b>Foydalanuvchilar ro'yxati</b> (Jami: {total_users})\n\n"
    if not users:
        text += "Foydalanuvchilar topilmadi."
    else:
        for i, user in enumerate(users, offset + 1):
            uid, fname, uname, reg_at, ref_id, ref_name = user
            safe_fname = html.escape(fname or "Ism yo'q")
            uname_display = f"@{html.escape(uname)}" if uname else "yo'q"
            reg_date = reg_at.split()[0] if reg_at else "-"
            
            user_line = f"{i}. 👤 <b>{safe_fname}</b> ({uname_display})\n"
            user_line += f"🆔 <code>{uid}</code> | 📅 {reg_date}\n"
            if ref_id:
                safe_ref_name = html.escape(ref_name or "Ishtirokchi")
                user_line += f"🤝 Taklif qiluvchi: {safe_ref_name} (<code>{ref_id}</code>)\n"
            text += user_line + "\n"
        
    text += f"📄 Sahifa: {page} / {total_pages}"
    
    keyboard = []
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"admin_users_{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"admin_users_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
        
    keyboard.append([InlineKeyboardButton("⬆️ Statistikaga qaytish", callback_data="admin_back_stats")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def admin_region_stats_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if update.effective_user.id != admin_id:
        if query: query.answer("Ruxsat berilmagan")
        return
    
    if query: query.answer()
    
    region_stats = get_region_stats()
    total_with_region = sum(count for _, count in region_stats if _ != "Tanlanmagan ❓")
    
    text = "🗺 <b>Hududlar bo'yicha statistika</b>\n\n"
    
    if not region_stats:
        text += "Ma'lumotlar topilmadi."
    else:
        for region, count in region_stats:
            text += f"📍 {region}: <code>{count}</code>\n"
        
        text += f"\n📊 Hudud tanlaganlar: <code>{total_with_region}</code>"

    keyboard = [[InlineKeyboardButton("⬆️ Statistikaga qaytish", callback_data="admin_back_stats")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

def admin_back_stats_callback(update: Update, context: CallbackContext):
    return admin_stats_command(update, context)
