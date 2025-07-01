from Suralar.navigate_ayahs import play_surah_audio, navigate_ayahs, play_ayah_audio
from Suralar.show_ayah_text import show_ayah_text
from Suralar.show_specific_ayah import show_specific_ayah
from Suralar.show_surah_details import show_surah_details
from Suralar.show_translation import show_ayah_list, show_translation
from Suralar.user_main_menu import user_main_menu
from telegram import Update
from telegram.ext import CallbackContext
from Suralar.menu_button import logger


def button_handler(update: Update, context: CallbackContext):
    """Barcha inline tugmalar uchun yaxshilangan ishlovchi funksiya"""
    try:
        query = update.callback_query
        query.answer()  # Callback query uchun darhol javob
        data = query.data
        user_data = context.user_data

        # Message ID ni saqlash
        if query.message:
            user_data['last_message_id'] = query.message.message_id

        # ===== NAVIGATION HANDLERS =====
        if data in ['next_page', 'prev_page', 'next_surah_page', 'prev_surah_page']:
            handle_pagination(data, user_data, update, context)

        elif data.startswith("sura_"):
            handle_surah_selection(data, user_data, query, context)

        elif data.startswith("ayah_"):
            handle_ayah_selection(data, user_data, query, context)

        elif data in ['next_translation', 'prev_translation']:
            handle_translation_navigation(data, user_data, query, context)

        elif data.startswith("back_to_"):
            handle_back_navigation(data, user_data, query, context)

        elif data in ['list_ayahs', 'next_page_ayahs', 'prev_ayah_page']:
            handle_ayah_list_navigation(data, user_data, query, context)

        elif data in ['list_surahs', 'show_surahs_list']:
            handle_surah_list_navigation(user_data, update, context)

        # ===== CONTENT DISPLAY HANDLERS =====
        elif data == 'show_text':
            handle_show_text(user_data, query, context)

        elif data == 'translation_ayah':
            handle_translation(user_data, query, context)

        elif data == 'audio_surah':
            handle_surah_audio(user_data, query, context)

        elif data == 'audio_ayah':
            handle_ayah_audio(user_data, query, context)

        elif data in ['previous_ayah', 'next_ayah']:
            handle_ayah_navigation(data, user_data, query, context)

        else:
            handle_unknown_button(query)

    except Exception as e:
        logger.error(f"Tugma ishlovchisida xato ")


# ===== HELPER FUNCTIONS =====
def handle_translation_navigation(data, user_data, query, context):
    """Tarjimalar orasida harakatlanish"""
    if 'current_surah' not in user_data:
        query.answer("❗️ Avval surani tanlang", show_alert=True)
        return

    current_ayah = user_data.get('translation_ayah', user_data.get('current_ayah', 1))

    if data == 'next_translation':
        user_data['translation_ayah'] = current_ayah + 1
    elif data == 'prev_translation':
        user_data['translation_ayah'] = max(1, current_ayah - 1)

    show_translation(query, context)


def handle_pagination(data, user_data, update, context):
    """Sahifalash tugmalarini boshqarish"""
    page_type = 'current_page' if 'page' in data else 'surah_page'
    increment = 1 if 'next' in data else -1

    user_data[page_type] = max(0, user_data.get(page_type, 0) + increment)
    user_main_menu(update, context)


def handle_surah_selection(data, user_data, query, context):
    """Sura tanlashni boshqarish"""
    surah_num = int(data.split('_')[1])
    user_data.update({
        'surah_pages_sec': surah_num,
        'current_surah': surah_num,
        'current_ayah': 1,
        'translation_ayah': 1,  # Reset to first ayah
        'ayah_page': 0,
        'last_btn': 0
    })
    show_surah_details(query, context)


def handle_ayah_selection(data, user_data, query, context):
    """Oyat tanlashni boshqarish"""
    _, surah_num, ayah_num = data.split('_')
    ayah_num = int(ayah_num)
    user_data.update({
        'current_surah': int(surah_num),
        'current_ayah': ayah_num,
        'translation_ayah': ayah_num  # Tanlangan oyatga tarjimani ham o'rnatish
    })
    show_specific_ayah(query, context)


def handle_back_navigation(data, user_data, query, context):
    """Orqaga qaytish tugmalarini boshqarish"""
    surah_num = int(data.split('_')[2])
    user_data['surah_pages_sec'] = surah_num
    show_surah_details(query, context)


def handle_ayah_list_navigation(data, user_data, query, context):
    """Oyatlar ro'yxati navigatsiyasini boshqarish"""
    if 'surah_pages_sec' not in user_data:
        query.answer("❗️ Avval surani tanlang", show_alert=True)
        return

    if data == 'list_ayahs':
        user_data.update({
            'ayah_page': 0,
            'last_btn': 0,
            'current_ayah': 1
        })
    elif data == 'next_page_ayahs':
        user_data['ayah_page'] = user_data.get('ayah_page', 0) + 1
    elif data == 'prev_ayah_page':
        user_data['ayah_page'] = max(0, user_data.get('ayah_page', 0) - 1)

    show_ayah_list(query, context)


def handle_surah_list_navigation(user_data, update, context):
    """Suralar ro'yxatiga qaytish"""
    user_data.update({
        'current_page': 0,
        'surah_page': 0,
        'ayah_page': 0
    })
    user_main_menu(update, context)


def handle_show_text(user_data, query, context):
    """Matn ko'rsatishni boshqarish"""
    if 'surah_pages_sec' not in user_data:
        query.answer("❗️ Avval surani tanlang", show_alert=True)
        return

    user_data['current_ayah'] = user_data.get('current_ayah', 1)
    show_ayah_text(query, context)


def handle_translation(user_data, query, context):
    """Tarjima ko'rsatishni boshqarish"""
    if 'current_surah' not in user_data:
        query.answer("❗️ Avval surani tanlang", show_alert=True)
        return

    # current_ayah mavjud bo'lsa, shu oyatni ko'rsatish
    user_data['translation_ayah'] = user_data.get('current_ayah', 1)
    show_translation(query, context)


def handle_surah_audio(user_data, query, context):
    """Sura audiosini boshqarish"""
    if 'surah_pages_sec' not in user_data:
        query.answer("❗️ Avval surani tanlang", show_alert=True)
        return

    play_surah_audio(query, context)


def handle_ayah_audio(user_data, query, context):
    """Oyat audiosini boshqarish"""
    if 'current_surah' not in user_data or 'current_ayah' not in user_data:
        query.answer("❗️ Avval oyatni tanlang", show_alert=True)
        return

    try:
        play_ayah_audio(query, context)
    except Exception as e:
        logger.error(f"Oyat audiosini yuborishda xato: {str(e)}")
        query.answer("❗️ Audio yuborishda xatolik", show_alert=True)


def handle_ayah_navigation(data, user_data, query, context):
    """Oyatlar orasida harakatlanishni boshqarish"""
    if 'surah_pages_sec' not in user_data or 'current_ayah' not in user_data:
        query.answer("❗️ Avval oyatni tanlang", show_alert=True)
        return

    navigate_ayahs(query, context, data)


def handle_unknown_button(query):
    """Noma'lum tugmalarni boshqarish"""
    query.answer("❗️ Ushbu funksiya hozircha mavjud emas", show_alert=True)


def handle_button_error(query, context, error):
    """Xatoliklarni boshqarish uchun yordamchi funksiya"""
    error_msg = "⚠️ Xatolik yuz berdi. Iltimos, qayta urunib ko'ring."

    try:
        if hasattr(query, 'message') and query.message:
            if query.message.photo:
                query.edit_message_caption(caption=error_msg)
            else:
                query.edit_message_text(error_msg)
    except:
        try:
            context.bot.send_message(
                chat_id=query.from_user.id,
                text=error_msg
            )
        except Exception as final_error:
            logger.error(f"Yakuniy xato boshqaruvchi ham ishlamadi: {str(final_error)}")
