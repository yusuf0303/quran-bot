from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from Suralar.menu_button import logger


def show_next_ayahs_page(query, context):
    """Keyingi sahifani ko'rsatish"""
    try:
        query.answer()
        datas = context.user_data
        surah_num = datas.get('surah_pages_sec', 1)
        last_btn = datas.get('last_btn', 0)
        total_ayahs = datas.get('total_ayahs', 114)  # Default 114

        # Yangi boshlang'ich va tugash indekslari
        start_btn = last_btn + 48
        end_btn = min(start_btn + 48, total_ayahs)

        # Tugmalarni yaratish
        buttons = [
            InlineKeyboardButton(str(i + 1), callback_data=f"ayah_{surah_num}_{i + 1}")
            for i in range(start_btn, end_btn)
        ]

        # Tugmalarni joylashtirish
        keyboard = [buttons[i:i + 8] for i in range(0, len(buttons), 8)]

        # Navigatsiya tugmalari
        nav_buttons = []
        if start_btn > 0:  # Orqaga tugmasi
            nav_buttons.append(InlineKeyboardButton("⬅️ Orqaga", callback_data="prev_ayah_page"))
        if end_btn < total_ayahs:  # Keyingi tugmasi
            nav_buttons.append(InlineKeyboardButton("Keyingi ➡️", callback_data="next_page_ayahs"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        # Doimiy tugmalar
        keyboard.append([
            InlineKeyboardButton("⬅️ Sura", callback_data=f"back_to_{surah_num}"),
            InlineKeyboardButton("📖 Suralar", callback_data="list_surahs")
        ])

        # Faqat reply_markup ni yangilash - BU ENG MUHIM QISMI!
        try:
            query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(keyboard))
            datas['last_btn'] = start_btn
        except Exception as e:
            logger.error(f"Tugmalarni yangilashda xato: {e}")
            raise

    except Exception as e:
        logger.error(f"Keyingi sahifada xato: {e}")
        query.answer("⚠️ Keyingi sahifaga o'tishda xatolik", show_alert=True)


def show_prev_ayahs_page(query, context):
    """Oldingi sahifani ko'rsatish"""
    try:
        query.answer()
        datas = context.user_data
        surah_num = datas.get('surah_pages_sec', 1)
        last_btn = datas.get('last_btn', 48)  # Default 48
        total_ayahs = datas.get('total_ayahs', 114)

        # Yangi boshlang'ich va tugash indekslari
        start_btn = max(0, last_btn - 96)  # 2 sahifaga orqaga
        end_btn = start_btn + 48

        # Tugmalarni yaratish
        buttons = [
            InlineKeyboardButton(str(i + 1), callback_data=f"ayah_{surah_num}_{i + 1}")
            for i in range(start_btn, end_btn)
        ]

        # Tugmalarni joylashtirish
        keyboard = [buttons[i:i + 8] for i in range(0, len(buttons), 8)]

        # Navigatsiya tugmalari
        nav_buttons = []
        if start_btn > 0:  # Orqaga tugmasi
            nav_buttons.append(InlineKeyboardButton("⬅️ Orqaga", callback_data="prev_ayah_page"))
        if end_btn < total_ayahs:  # Keyingi tugmasi
            nav_buttons.append(InlineKeyboardButton("Keyingi ➡️", callback_data="next_page_ayahs"))

        if nav_buttons:
            keyboard.append(nav_buttons)

        # Doimiy tugmalar
        keyboard.append([
            InlineKeyboardButton("⬅️ Sura", callback_data=f"back_to_{surah_num}"),
            InlineKeyboardButton("📖 Suralar", callback_data="list_surahs")
        ])

        # Faqat reply_markup ni yangilash
        try:
            query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(keyboard))
            datas['last_btn'] = start_btn
        except Exception as e:
            logger.error(f"Tugmalarni yangilashda xato: {e}")
            raise

    except Exception as e:
        logger.error(f"Oldingi sahifada xato: {e}")
        query.answer("⚠️ Oldingi sahifaga o'tishda xatolik", show_alert=True)