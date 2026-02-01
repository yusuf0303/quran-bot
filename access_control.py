from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
from telegram.ext import CallbackContext
from Ramadan.contest_logic import check_subscription
from Suralarni_toping.database import is_user_confirmed

def ensure_access(update: Update, context: CallbackContext) -> bool:
    """Checks if user has confirmed terms and is subscribed to channels."""
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id: return True # Non-user events
    
    # 1. Check Terms from database (persistent across bot restarts)
    confirmed = is_user_confirmed(user_id)
    
    # 2. Check Subscription
    subscribed = check_subscription(context.bot, user_id)
    
    if confirmed and subscribed:
        return True
        
    # If not, show access denied / terms prompt
    show_access_denied(update, context, not subscribed)
    return False

def show_access_denied(update, context, subscription_needed=False):
    keyboard = [
        [InlineKeyboardButton(text="📋 Foydalanish shartlari", url="https://t.me/KalomUz_News/4")],
    ]
    
    if subscription_needed:
        keyboard.append([InlineKeyboardButton(text="➕ Kanalga obuna bo'lish", url="https://t.me/KalomUz_News")])
        
    keyboard.append([InlineKeyboardButton(text="Tasdiqlayman ✅", callback_data="confirm_terms")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user_name = update.effective_user.full_name if update.effective_user else "Foydalanuvchi"
    
    if subscription_needed:
        text = (
            f"Assalomu alaykum, {user_name}!\n"
            "Botdan foydalanish uchun quyidagi shartlarni bajaring:\n\n"
            "1. @KalomUz_News kanaliga a'zo bo'ling.\n"
            "2. Foydalanish shartlari bilan tanishib chiqing.\n\n"
            "So'ng 'Tasdiqlayman ✅' tugmasini bosing."
        )
    else:
        text = (
            f"Assalomu alaykum, {user_name}!\n"
            "Online Qur'on botiga xush kelibsiz 🤗\n\n"
            "Botdan to'liq foydalanish uchun foydalanish shartlari bilan tanishib chiqing va tasdiqlang:"
        )
    
    if update.callback_query:
        update.callback_query.answer("Iltimos, avval ro'yxatdan o'ting!", show_alert=True)
        try:
            update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        except:
            context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)
    else:
        update.message.reply_text(text, reply_markup=reply_markup)
