from telegram import InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from Masjidlar.get_mosques import setup_mosque_handlers
from SchedulerAyah.scheduler import start_daily_ayah_scheduler
from Suralar.error_handler import error_handler
from Suralar.menu_button import main_buttons
from Suralar.user_main_menu import user_main_menu
from Suralarni_toping.database import register_user, get_all_user_ids
from Suralarni_toping.sura_game import setup_handlers
from namoz_vaqtlari.time_namoz import setup_prayer_times_handlers
import os
import logging
from dotenv import load_dotenv
from inline_quran import setup_inline_handlers
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, PollAnswerHandler
from Quiz.quiz_creator import setup_quiz_handlers, handle_poll_answer
from Suralar.button_handler import button_handler

load_dotenv()
logger = logging.getLogger(__name__)

def start_bot(update, context):
    context.user_data['confirmed'] = False
    user = update.effective_user
    register_user(user)
    
    commands = [
        BotCommand(command='start', description="Botni ishga tushirish"),
        BotCommand(command='help', description="Yordam olish")
    ]
    context.bot.set_my_commands(commands)

    if context.args and context.args[0].startswith("quiz_"):
        try:
            from Quiz.quiz_creator import QuizCreator, prepare_quiz_questions, send_quiz_question
            from Suralarni_toping.database import get_shared_quiz
            
            raw_id = context.args[0].replace("quiz_", "")
            db_quiz = get_shared_quiz(raw_id)
            
            quiz = QuizCreator()
            quiz.user_full_name = update.effective_user.full_name
            
            if db_quiz:
                # Load existing quiz from DB
                quiz.selected_juz = [int(j) for j in db_quiz['juz_str'].split("-")]
                quiz.question_count = db_quiz['question_count']
                quiz.time_limit = db_quiz['time_limit']
                quiz.questions = db_quiz['questions']
                context.user_data['quiz_creator'] = quiz
                send_quiz_question(update, context)
                return
            else:
                # Fallback: maybe it's just settings (for backward compatibility or manual typing)
                parts = raw_id.split("_")
                if len(parts) >= 3:
                    juzs = [int(j) for j in parts[0].split("-")]
                    count = int(parts[1])
                    limit = int(parts[2])
                    
                    quiz.selected_juz = juzs
                    quiz.question_count = count
                    quiz.time_limit = limit
                    context.user_data['quiz_creator'] = quiz
                    
                    if prepare_quiz_questions(quiz):
                        send_quiz_question(update, context)
                        return
        except Exception as e:
            logger.error(f"Quiz deep link error: {e}")

    share_button = InlineKeyboardButton(
        "Do'stlarga ulashish ⤴️",
        switch_inline_query="👈 Ushbu botga kiring va Qur'onni yod oling!"
    )
    keyboard = InlineKeyboardMarkup([[share_button]])

    update.message.reply_text(
        f"Assalomu alaykum, {update.message.from_user.full_name}!\n"
        "Online Qur'on botiga xush kelibsiz 🤗\n"
        "Botni yaqinlaringizga ham ulashing ☪️",
        reply_markup=keyboard
    )
    show_terms(update, context)

def show_terms(update, context):
    keyboard = [
        [InlineKeyboardButton(text="📋 Foydalanish shartlari", url="https://t.me/KalomUz_News/4")],
        [InlineKeyboardButton(text="Tasdiqlayman ✅", callback_data="confirm_terms")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Botdan to'liq foydalanish uchun foydalanish shartlari bilan tanishib chiqing va tasdiqlang:",
        reply_markup=reply_markup
    )

def terms_confirmation(update, context):
    query = update.callback_query
    query.answer()
    if query.data == "confirm_terms":
        context.user_data['confirmed'] = True
        query.edit_message_text("Foydalanish shartlari qabul qilindi! Asosiy menyuga o'tishingiz mumkin.")
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Quyidagi bo'limlardan birini tanlang 👇",
            reply_markup=main_buttons()
        )

def help_command(update, context):
    help_text = (
        "🆘 *KalomUz 📖 Bot yordam bo‘limi*\n\n"
        "Assalomu alaykum! Ushbu bot orqali siz Qur’on oyatlari, suralari va namoz vaqtlari haqida tez va qulay ma’lumot olishingiz mumkin.\n\n"
        "📝 *Quiz yaratish*\n"
        "– O'zingiz xohlagan juzlardan xohlagan miqdorda savollar bilan quiz yaratishingiz mumkin.\n"
        "– Har bir savol uchun vaqt belgilashingiz mumkin.\n\n"
        "📚 *Suralar*\n"
        "– 114 ta sura ro‘yxati, matni, tarjimasi va audiosi.\n"
        "🧠 *Oyatlar o‘yini*\n"
        "– Oyat qaysi suradan ekanini topish o'yini.\n"
        "🕋 *Namoz vaqtlari*\n"
        "– O‘zbekiston bo‘yicha namoz vaqtlari.\n\n"
        "Hoziroq /start ni bosing!"
    )
    update.message.reply_text(help_text, parse_mode='Markdown')

def handle_invalid_message(update, context):
    if not context.user_data.get('confirmed', False):
        update.message.reply_text("Iltimos, avval foydalanish shartlarini tasdiqlang. ✅", reply_markup=show_terms(update, context))
    else:
        update.message.reply_text(
            f"Hurmatli {update.effective_user.first_name}, botdan foydalanish uchun quyidagi tugmalardan foydalaning.👇",
            reply_markup=main_buttons()
        )

def main():
    bot_token = os.getenv("BOT_TOKEN")
    start_daily_ayah_scheduler(bot_token)
    updater = Updater(bot_token, use_context=True, request_kwargs={'connect_timeout': 20, 'read_timeout': 20})
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_bot))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(terms_confirmation, pattern="^confirm_terms$"))
    dp.add_handler(MessageHandler(Filters.regex("^Suralar 🔍$"), user_main_menu))
    dp.add_error_handler(error_handler)
    setup_quiz_handlers(dp)
    dp.add_handler(PollAnswerHandler(handle_poll_answer))
    setup_handlers(dp)
    setup_inline_handlers(dp)
    setup_prayer_times_handlers(dp)
    setup_mosque_handlers(dp)
    dp.add_handler(CallbackQueryHandler(button_handler))  # Catch-all for Suralar section
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_invalid_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
