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
from dotenv import load_dotenv
from inline_quran import setup_inline_handlers

load_dotenv()


def start_bot(update, context):
    context.user_data['confirmed'] = False  # boshlanishda tasdiqlanmagan

    user = update.effective_user
    register_user(user)
    print(get_all_user_ids())

    commands = [
        BotCommand(command='start', description="Botni ishga tushirish"),
        BotCommand(command='help', description="Yordam olish")
    ]
    context.bot.set_my_commands(commands)

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
        context.user_data['confirmed'] = True  # Tasdiqlangan deb belgilaymiz

        query.edit_message_text("Foydalanish shartlari qabul qilindi! Asosiy menyuga o'tishingiz mumkin.")
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Quyidagi bo'limlardan birini tanlang 👇",
            reply_markup=main_buttons()
        )


def help_command(update, context):
    help_text = (
        "🆘 *KalomUz 📖 Bot yordam bo‘limi*\n\n"
        "Assalomu alaykum! Ushbu bot orqali siz Qur’on oyatlari, suralari va namoz vaqtlari haqida tez va qulay ma’lumot olishingiz mumkin. Quyidagi menyular orqali harakat qiling:\n\n"

        "📚 *Suralar*\n"
        "– 114 ta sura ro‘yxati.\n"
        "– Har bir sura haqida:\n"
        "  🔹 *Matn* — oyatlarning matni, tarjimasi va audiosi.\n"
        "  🔹 *Audio* — suraning to‘liq audiosi.\n"
        "  🔹 *Oyatlar* — suradagi barcha oyatlar ro‘yxati sahifalangan holda.\n\n"

        "🧠 *Oyatlar o‘yini*\n"
        "– Qur’ondan oyat beriladi va siz u qaysi suraga tegishli ekanini topasiz.\n"
        "– Har bir savolda 4 ta javob varianti bo‘ladi.\n"
        "– O‘yin davomida:\n"
        "  🎯 *To‘xtatish*\n"
        "  📊 *Natijalarni ko‘rish* funksiyalari mavjud.\n\n"

        "🕋 *Namoz vaqtlari*\n"
        "– O‘zbekistonning barcha viloyat va tumanlari bo‘yicha namoz vaqtlari.\n"
        "– Bosqichma-bosqich tanlash:\n"
        "  1️⃣ *Viloyat*\n"
        "  2️⃣ *Tuman*\n"
        "  3️⃣ *Namoz turi*:\n"
        "     🕓 *Bomdod, Peshin, Asr, Shom, Xufton*\n"
        "     📅 *Kunlik va Haftalik jadval*\n\n"

        "Agar sizda muammo yoki taklif bo‘lsa, biz bilan bog‘laning:\n"
        "🤝 [@KalomUzSupportBot](https://t.me/KalomUzSupportBot)\n\n"
        "Yordam kerak bo‘lsa, har doim /help ni bosishingiz mumkin.\n"
        "*KalomUz 📖 — ilmingizga ilm qo‘shadi!*"
    )
    update.message.reply_text(help_text, parse_mode='Markdown')


def handle_invalid_message(update, context):
    if not context.user_data.get('confirmed', False):
        update.message.reply_text("Iltimos, avval foydalanish shartlarini tasdiqlang. ✅", reply_markup=show_terms(update, context))
    else:
        user_name = update.effective_user.first_name
        update.message.reply_text(
            f"Hurmatli {user_name}, botdan foydalanish uchun quyidagi tugmalardan foydalaning.👇",
            reply_markup=main_buttons()
        )


# def start_random_ayah_scheduler(bot):
#     """Har kuni random vaqtda oyat yuborish uchun scheduler"""
#     # scheduler = BackgroundScheduler(timezone=utc)
#     # tz = timezone("Asia/Tashkent")
#     # scheduler = BackgroundScheduler()
#     # Random vaqt: 04:00 – 20:00 oralig‘idan
#     soat = random.randint(15, 16)
#     daqiqa = random.randint(15, 30)
#
#     trigger = CronTrigger(hour=soat, minute=daqiqa)
#     scheduler.add_job(
#         lambda: send_daily_random_ayah_to_all_users(bot),
#         trigger=trigger
#     )
#     print(f"📅 Random oyat scheduler sozlandi: har kuni {soat:02d}:{daqiqa:02d} da")
#     scheduler.start()


def main():
    bot_token = os.getenv("BOT_TOKEN")
    start_daily_ayah_scheduler(bot_token)
    updater = Updater(bot_token, use_context=True, request_kwargs={
        'connect_timeout': 20,
        'read_timeout': 20
    })

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start_bot))
    dp.add_handler(CommandHandler("help", help_command))

    dp.add_handler(CallbackQueryHandler(terms_confirmation, pattern="^confirm_terms$"))
    dp.add_handler(MessageHandler(Filters.regex("^Suralar 🔍$"), user_main_menu))

    dp.add_error_handler(error_handler)
    setup_handlers(dp)
    setup_inline_handlers(dp)
    setup_prayer_times_handlers(dp)
    setup_mosque_handlers(dp)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_invalid_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

#
# """
# pasdagi kodlar tasdiqlash tugmasi bolmasdan oldin yozilga edi
# """
# from telegram import InlineKeyboardButton,ReplyKeyboardMarkup, InlineKeyboardMarkup, BotCommand
# from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, filters, CallbackQueryHandler
#
# from Suralar import error_handler
# from Suralar.menu_button import main_buttons
#
#
# from Suralar.user_main_menu import user_main_menu
# from Suralarni_toping.sura_game import setup_handlers
# from namoz_vaqtlari.time_namoz import setup_prayer_times_handlers
# import os
# from dotenv import load_dotenv
# load_dotenv()
#
# def start_bot(update, context):
#     context.user_data['confirmed'] = False  # boshlanishda tasdiqlanmagan
#
#     commands = [
#         BotCommand(command='start', description="Botni ishga tushirish"),
#         BotCommand(command='help', description="Yordam olish")
#     ]
#     context.bot.set_my_commands(commands)
#
#     share_button = InlineKeyboardButton(
#         "Do'stlarga ulashish ⤴️",
#         switch_inline_query="👈 Ushbu botga kiring va Qur'onni yod oling!"
#     )
#     keyboard = InlineKeyboardMarkup([[share_button]])
#
#     update.message.reply_text(
#         f"Assalomu alaykum, {update.message.from_user.full_name}!\n"
#         "Online Qur'on botiga xush kelibsiz 🤗\n"
#         "Botni yaqinlaringizga ham ulashing ☪️",
#         reply_markup=keyboard
#     )
#     show_terms(update, context)
#
#
# def help_command(update, context):
#     help_text = (
#         "🆘 *KalomUz 📖 Bot yordam bo‘limi*\n\n"
#         "Assalomu alaykum! Ushbu bot orqali siz Qur’on oyatlari, suralari va namoz vaqtlari haqida tez va qulay ma’lumot olishingiz mumkin. Quyidagi menyular orqali harakat qiling:\n\n"
#
#         "📚 *Suralar*\n"
#         "– 114 ta sura ro‘yxati.\n"
#         "– Har bir sura haqida:\n"
#         "  🔹 *Matn* — oyatlarning matni, tarjimasi va audiosi.\n"
#         "  🔹 *Audio* — suraning to‘liq audiosi.\n"
#         "  🔹 *Oyatlar* — suradagi barcha oyatlar ro‘yxati sahifalangan holda.\n\n"
#
#         "🧠 *Oyatlar o‘yini*\n"
#         "– Qur’ondan oyat beriladi va siz u qaysi suraga tegishli ekanini topasiz.\n"
#         "– Har bir savolda 4 ta javob varianti bo‘ladi.\n"
#         "– O‘yin davomida:\n"
#         "  🎯 *To‘xtatish*\n"
#         "  📊 *Natijalarni ko‘rish* funksiyalari mavjud.\n\n"
#
#         "🕋 *Namoz vaqtlari*\n"
#         "– O‘zbekistonning barcha viloyat va tumanlari bo‘yicha namoz vaqtlari.\n"
#         "– Bosqichma-bosqich tanlash:\n"
#         "  1️⃣ *Viloyat*\n"
#         "  2️⃣ *Tuman*\n"
#         "  3️⃣ *Namoz turi*:\n"
#         "     🕓 *Bomdod, Peshin, Asr, Shom, Xufton*\n"
#         "     📅 *Kunlik va Haftalik jadval*\n\n"
#
#         "Agar sizda muammo yoki taklif bo‘lsa, biz bilan bog‘laning:\n"
#         "🤝 [@KalomUzSupportBot](https://t.me/KalomUzSupportBot)\n\n"
#         "Yordam kerak bo‘lsa, har doim /help ni bosishingiz mumkin.\n"
#         "*KalomUz 📖 — ilmingizga ilm qo‘shadi!*"
#     )
#     update.message.reply_text(help_text, parse_mode='Markdown')
#
# def show_terms(update, context):
#     keyboard = [
#         [InlineKeyboardButton(text="📋 Foydalanish shartlari", url="https://t.me/KalomUz_News/4")],
#         [InlineKeyboardButton(text="Tasdiqlayman ✅", callback_data="confirm_terms")]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     update.message.reply_text(
#         "Botdan to'liq foydalanish uchun foydalanish shartlari bilan tanishib chiqing va tasdiqlang:",
#         reply_markup=reply_markup
#     )
# def terms_confirmation(update, context):
#     query = update.callback_query
#     query.answer()
#
#     if query.data == "confirm_terms":
#         context.user_data['confirmed'] = True  # Tasdiqlangan deb belgilaymiz
#
#         query.edit_message_text("Foydalanish shartlari qabul qilindi! Asosiy menyuga o'tishingiz mumkin.")
#         context.bot.send_message(
#             chat_id=query.message.chat_id,
#             text="Quyidagi bo'limlardan birini tanlang 👇",
#             reply_markup=main_buttons()
#         )
# def handle_invalid_message(update, context):
#     if not context.user_data.get('confirmed', False):
#         update.message.reply_text("Iltimos, avval foydalanish shartlarini tasdiqlang. ✅")
#     else:
#         user_name = update.effective_user.first_name
#         update.message.reply_text(
#             f"Hurmatli {user_name}, botdan foydalanish uchun faqat tugmalardan foydalaning. 👆"
#         )
#
#
# def main():
#     Bot_token=os.getenv("BOT_TOKEN")
#     updater = Updater(Bot_token, use_context=True,request_kwargs={
#     'connect_timeout': 20,
#     'read_timeout': 20
# })
#     dp = updater.dispatcher
#
#     # Asosiy handlerlar
#     dp.add_handler(CommandHandler("start", start_bot))
#     dp.add_handler(CommandHandler("help",help_command))
#     dp.add_handler(MessageHandler(Filters.regex("^Suralar 🔍$"), user_main_menu))
#     dp.add_handler(CallbackQueryHandler(terms_confirmation, pattern="^confirm_terms$"))
#     dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_invalid_message))
#
#     dp.add_error_handler(error_handler)
#     setup_handlers(dp)
#     setup_prayer_times_handlers(dp)
#     updater.start_polling()
#     updater.idle()
#
#
# if __name__ == '__main__':
#     main()

# #
