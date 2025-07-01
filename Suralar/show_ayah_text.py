import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from Suralar.API_lar import QURAN_API
from Suralar.menu_button import logger


def show_ayah_text(query, context):
    """Oyat matnini ko'rsatish"""
    try:
        query.answer("Oyat sahifasi yuklanmoqda...")
        try:
            query.delete_message()
        except:
            pass

        user_id = query.from_user.id
        datas = context.user_data
        num_of_surah = datas.get('surah_pages_sec',1)

        if not num_of_surah:
            context.bot.send_message(chat_id=user_id, text="❗️ Avval surani tanlang.")
            return

        response = requests.get(f"{QURAN_API}/surah/{num_of_surah}", timeout=20)
        response.raise_for_status()
        surah_data = response.json()['data']

        ayah = surah_data['ayahs'][0]  # faqat birinchi oyat
        surah_num = surah_data['number']
        eng_name = surah_data['englishName']
        number_of_ayah = surah_data['numberOfAyahs']

        image_url = f"https://cdn.islamic.network/quran/images/high-resolution/{surah_num}_{ayah['numberInSurah']}.png"
        image_response = requests.get(image_url, timeout=10)

        res_sajda = " emas‼️" if str(ayah['sajda']) == 'False' else "‼️"

        caption = (
            f"<code>🔹{eng_name} - surasi [ {ayah['numberInSurah']} | {number_of_ayah} ]\n"
            f"🔹Surada: {ayah['numberInSurah']} - oyat\n"
            f"🔹Quronda: {ayah['number']} - oyat\n"
            f"🔹Juz: {ayah['juz']}\n"
            f"🔹Sahifa: {ayah['page']}\n"
            f"⚠️ Ushbu oyat Sajda oyati{res_sajda}\n"
            f"🔹Oyat matni 👇\n{ayah['text']}</code>"
        )

        buttons = [
            [
                InlineKeyboardButton("Audio 🎧", callback_data=f'audio_{surah_num}_{ayah["numberInSurah"]}'),
                InlineKeyboardButton(f"{ayah['numberInSurah']} | {number_of_ayah}", callback_data='current_ayah'),
                InlineKeyboardButton("Tarjima 📄", callback_data=f'translation_{surah_num}_{ayah["numberInSurah"]}')
            ]
        ]
        nav_buttons = []
        if ayah['numberInSurah'] > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data='previous_ayah'))
        if ayah['numberInSurah'] < number_of_ayah:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data='next_ayah'))
        if nav_buttons:
            buttons.append(nav_buttons)

        buttons.append([
            InlineKeyboardButton("⬅️ Sura", callback_data=f'back_to_{surah_num}'),
            InlineKeyboardButton("📖 Suralar", callback_data='list_surahs')  # O'zgartirildi
        ])
        control = InlineKeyboardMarkup(buttons)

        if image_response.status_code == 200:
            if len(caption) <= 1000:
                context.bot.send_photo(
                    chat_id=user_id,
                    photo=image_response.content,
                    caption=caption,
                    reply_markup=control,
                    parse_mode="HTML"
                )
            else:
                caption_chunks = [caption[i:i + 1000] for i in range(0, len(caption), 1000)]
                photo_msg = context.bot.send_photo(
                    chat_id=user_id,
                    photo=image_response.content,
                    caption=caption_chunks[0],
                    parse_mode="HTML"
                )
                context.bot.send_message(
                    chat_id=user_id,
                    text=caption_chunks[1],
                    reply_markup=control,
                    parse_mode="HTML"
                )
                context.user_data['part_1_id'] = photo_msg.message_id
        else:
            context.bot.send_message(
                chat_id=user_id,
                text=caption,
                reply_markup=control,
                parse_mode="HTML"
            )

        datas['current_ayah'] = ayah['numberInSurah']
        datas['current_surah'] = surah_num
        datas['translation_ayah'] = ayah['number']

    except Exception as e:
        logger.error(f"show_ayah_text xatosi: {e}")
        try:
            query.edit_message_text("⚠️ Oyat matni yuklanmadi.")
        except:
            context.bot.send_message(
                chat_id=query.from_user.id,
                text="⚠️ Oyat matni yuklanmadi."
            )
