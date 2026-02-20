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
from Ramadan.handlers import konkurs_command, leaderboard_callback, reyting_command, set_region_callback, save_region_callback, insta_verify_callback, ramadan_back_callback, juma_test_command
from Admin.stats import admin_stats_command, admin_users_callback, admin_back_stats_callback, admin_region_stats_callback
from namoz_vaqtlari.scheduler import start_prayer_scheduler
from Ramadan.database import add_referral
from Ramadan.contest_logic import get_leaderboard_text
from access_control import ensure_access, show_access_denied
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="telegram.ext.conversationhandler")

load_dotenv()
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="telegram.ext.conversationhandler")

logger = logging.getLogger(__name__)

def start_bot(update, context):
    user = update.effective_user
    register_user(user)
    
    commands = [
        BotCommand(command='start', description="Botni ishga tushirish"),
        BotCommand(command='konkurs', description="Ramazon konkursi (Dashboard)"),
        BotCommand(command='reyting', description="Umumiy peshqadamlar ro'yxati"),
        BotCommand(command='hudud', description="Saharlik/Iftor vaqtini belgilash"),
        BotCommand(command='juma_test', description="Juma testi (Haftalik)"),
        BotCommand(command='help', description="Yordam olish")
    ]
    context.bot.set_my_commands(commands)
    
    # Check for referral bonus (if user is new and joined via r123)

    # Check for referral deep link
    args = context.args
    user_id = update.effective_user.id
    if args and args[0].startswith('r'):
        try:
            referrer_id = int(args[0][1:])
            if referrer_id != user_id:
                add_referral(referrer_id, user_id)
        except Exception:
            pass

    if args and args[0].startswith("quiz_"):
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
                quiz.quiz_id = raw_id
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
                        quiz.quiz_id = raw_id
                        send_quiz_question(update, context)
                        return
        except Exception:
            pass
    
    # Check subscription and terms immediately
    from Ramadan.contest_logic import check_subscription
    from Suralarni_toping.database import is_user_confirmed
    is_subscribed = check_subscription(context.bot, user_id)
    confirmed = is_user_confirmed(user_id)
    
    if not confirmed or not is_subscribed:
        show_access_denied(update, context, subscription_needed=not is_subscribed)
        return

    # If already confirmed and subscribed, show main menu or handle deep link
    # (Deep link logic above already handles return if quiz found)
    update.message.reply_text(
        f"Assalomu alaykum, {update.effective_user.full_name}! Botga qaytganingizdan xursandmiz. 😊",
        reply_markup=main_buttons(user_id)
    )

# Logic moved to access_control.py

def show_terms(update, context):
    show_access_denied(update, context)

def terms_confirmation(update, context):
    query = update.callback_query
    query.answer()
    if query.data == "confirm_terms":
        from Suralarni_toping.database import set_user_confirmed
        from Ramadan.contest_logic import check_subscription
        
        # Save confirmation to database (persistent)
        set_user_confirmed(update.effective_user.id, True)
        
        # Also check subscription again to be sure
        if not check_subscription(context.bot, update.effective_user.id):
            return show_access_denied(update, context, subscription_needed=True)
            
        query.edit_message_text("Tabriklaymiz! Ro'yxatdan o'tish muvaffaqiyatli yakunlandi. ✅")
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Quyidagi bo'limlardan birini tanlang 👇\n\n🏆 Ramazon konkursida ishtirok etish uchun /konkurs buyrug'ini bosing! 🌙",
            reply_markup=main_buttons(update.effective_user.id)
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
    if not ensure_access(update, context):
        return
    
    msg = update.effective_message
    if msg:
        msg.reply_text(
            f"Hurmatli {update.effective_user.first_name}, botdan foydalanish uchun quyidagi tugmalardan foydalaning.👇",
            reply_markup=main_buttons(update.effective_user.id)
        )

def main():
    bot_token = os.getenv("BOT_TOKEN")
    start_daily_ayah_scheduler(bot_token)
    
    updater = Updater(bot_token, use_context=True, request_kwargs={'connect_timeout': 20, 'read_timeout': 20})
    from Ramadan.scheduler import start_ramadan_scheduler
    start_ramadan_scheduler(updater.bot)
    start_prayer_scheduler(updater.bot)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start_bot))
    dp.add_handler(CommandHandler("help", help_command))
    
    # Wrapped CommandHandlers
    def wrapped_handler(handler_func):
        def wrapper(update, context):
            if ensure_access(update, context):
                return handler_func(update, context)
        return wrapper

    dp.add_handler(CommandHandler("konkurs", wrapped_handler(konkurs_command)))
    dp.add_handler(CommandHandler("reyting", wrapped_handler(reyting_command)))
    dp.add_handler(CommandHandler("stats", admin_stats_command))
    dp.add_handler(CommandHandler("users", admin_users_callback))
    dp.add_handler(MessageHandler(Filters.regex("^Admin ⚙️$"), admin_stats_command))
    dp.add_handler(MessageHandler(Filters.regex("^Foydalanuvchilar ro'yxati 👥$"), admin_users_callback))
    dp.add_handler(CommandHandler("hudud", wrapped_handler(set_region_callback)))
    dp.add_handler(CommandHandler("juma_test", wrapped_handler(juma_test_command)))
    dp.add_handler(MessageHandler(Filters.regex("^Konkurs 🏆$"), wrapped_handler(konkurs_command)))
    
    # Ramadan Callbacks (Wrapped)
    dp.add_handler(CallbackQueryHandler(wrapped_handler(leaderboard_callback), pattern=r"^ramadan_leaderboard(_\d+)?$"))
    dp.add_handler(CallbackQueryHandler(wrapped_handler(set_region_callback), pattern="^ramadan_set_region$"))
    dp.add_handler(CallbackQueryHandler(wrapped_handler(save_region_callback), pattern="^ramadan_save_reg_"))
    dp.add_handler(CallbackQueryHandler(wrapped_handler(insta_verify_callback), pattern="^ramadan_insta_verify$"))
    dp.add_handler(CallbackQueryHandler(wrapped_handler(ramadan_back_callback), pattern="^ramadan_back_to_status$"))
    
    # Admin Callbacks
    dp.add_handler(CallbackQueryHandler(admin_users_callback, pattern=r"^admin_users_\d+$"))
    dp.add_handler(CallbackQueryHandler(admin_region_stats_callback, pattern="^admin_region_stats$"))
    dp.add_handler(CallbackQueryHandler(admin_back_stats_callback, pattern="^admin_back_stats$"))
    
    # Friday Test Start Callback
    from Ramadan.quiz_integration import handle_friday_test_start
    dp.add_handler(CallbackQueryHandler(wrapped_handler(handle_friday_test_start), pattern="^start_friday_test$"))
    
    dp.add_handler(CallbackQueryHandler(terms_confirmation, pattern="^confirm_terms$"))
    dp.add_handler(MessageHandler(Filters.regex("^Suralar 🔍$"), wrapped_handler(user_main_menu)))
    dp.add_error_handler(error_handler)
    setup_quiz_handlers(dp)
    dp.add_handler(PollAnswerHandler(handle_poll_answer))
    setup_handlers(dp)
    setup_inline_handlers(dp)
    setup_prayer_times_handlers(dp) # These have internal checks or can be wrapped if they expose handlers
    setup_mosque_handlers(dp)
    
    # Update prayer photo file_id at startup for robustness
    try:
        admin_id = os.getenv("ADMIN_ID")
        if admin_id:
            photo_path = os.path.join("namoz_vaqtlari", "prayer_times.png")
            if os.path.exists(photo_path):
                with open(photo_path, 'rb') as f:
                    msg = updater.bot.send_photo(
                        chat_id=admin_id, 
                        photo=f, 
                        caption="✨ Bot ishga tushdi. Namoz vaqtlari rasmi inline query uchun yangilandi."
                    )
                    import inline_quran
                    inline_quran.PRAYER_PHOTO_FILE_ID = msg.photo[-1].file_id
                    logger.info(f"Yangi PRAYER_PHOTO_FILE_ID: {inline_quran.PRAYER_PHOTO_FILE_ID}")
    except Exception as e:
        logger.error(f"PRAYER_PHOTO_FILE_ID yangilashda xatolik: {e}")
    
    from admin_broadcast import setup_admin_handlers
    setup_admin_handlers(dp)
    
    dp.add_handler(CallbackQueryHandler(wrapped_handler(button_handler)))  # Catch-all for Suralar section
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_invalid_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
