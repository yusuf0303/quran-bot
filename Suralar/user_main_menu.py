import os

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

from Suralar.API_lar import QURAN_API, surah_list
from Suralar.menu_button import logger


def user_main_menu(update, context):
    try:
        # Sahifa raqamini olish
        current_page = context.user_data.get('current_page', 0)

        # Qur'on suralarini olish
        req = requests.get(url=f"{QURAN_API}/surah").json()
        surahs = req['data']

        # Suralarni saqlash (raqam + nom formatida)
        for i, s in enumerate(surahs):
            surah_list[i + 1] = f"{i + 1}. {s['englishName']}"  # Raqam va nom formatida

        # Sahifalash parametrlari
        per_page = 19
        total_surahs = len(surahs)
        start_index = current_page * per_page #cur_page imiz dastlab 0 qaysi index dan boshlashimiz muhim

        end_index = min((current_page + 1) * per_page, total_surahs)
        # bizga chiquvchi yani inline buttonlar qaysi suralar oralig'ida bolishi kerakligi malum boladi

        # Tugmalarni yaratish (3x6 formatda)
        buttons = []
        for i in range(start_index, end_index):#suralarimiz (1 to 114 gacha )
            surah_num = i + 1
            # Raqam va nom bilan tugma matni
            btn_text = f"{surah_num}. {surahs[i]['englishName']}"
            buttons.append(InlineKeyboardButton(
                text=btn_text,
                callback_data=f'sura_{surah_num}'
            ))

        # Navigatsiya tugmalari
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Oldingi", callback_data='prev_page'))
        if end_index < total_surahs:
            nav_buttons.append(InlineKeyboardButton("Keyingi ➡️", callback_data='next_page'))

        # Tugmalarni tartiblash (3 ta ustun)
        layout = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]  # 3 ta ustunni olib keyin qatorga otish
        if nav_buttons:
            layout.append(nav_buttons)
        reply_markup = InlineKeyboardMarkup(layout)

        # Xabar matni
        total_pages = (total_surahs + per_page - 1) // per_page  # To'g'ri sahifalar soni
        caption = f"📖 Qur'on suralari (Sahifa {current_page + 1}/{total_pages})"

        # Xabarni yuborish
        photo = "images/quran_karim.jpg"

        if update.callback_query:
            query = update.callback_query
            query.answer()
            if os.path.exists(photo):
                with open(photo, 'rb') as p:
                    query.edit_message_media(
                        media=InputMediaPhoto(media=p, caption=caption),
                        reply_markup=reply_markup
                    )
            else:
                query.edit_message_text(
                    text=caption,
                    reply_markup=reply_markup
                )
        elif update.message:
            if os.path.exists(photo):
                with open(photo, 'rb') as p:
                    update.message.reply_photo(
                        photo=p,
                        caption=caption,
                        reply_markup=reply_markup
                    )
            else:
                update.message.reply_text(
                    text=caption,
                    reply_markup=reply_markup
                )

    except Exception as e:
        logger.error(f"Surah list error: {e}")
        error_msg = "⚠️ Suralar ro'yxati yuklanmadi. Iltimos, keyinroq urinib ko'ring."
        if update.callback_query:
            update.callback_query.answer(error_msg)
        elif update.message:
            update.message.reply_text(error_msg)