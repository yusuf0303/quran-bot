import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaAudio
from Suralar.API_lar import QURAN_API
from Suralar.menu_button import logger
from Suralar.surah_ikb import surah_ikb, surah_ikb2

_AYAH_CACHE = {}


def get_surah_data(surah_num):
    """Sura ma'lumotlarini cache'da saqlash"""
    if surah_num not in _AYAH_CACHE:
        response = requests.get(f"{QURAN_API}/surah/{surah_num}", timeout=10)
        if response.status_code == 200:
            _AYAH_CACHE[surah_num] = response.json()['data']
    return _AYAH_CACHE.get(surah_num)


def show_ayah(query, context, ayah_number):
    """Bitta oyatni ko'rsatish (asosiy funksiya)"""
    try:
        datas = context.user_data
        surah_num = datas.get('surah_pages_sec')

        if not surah_num:
            context.bot.send_message(
                chat_id=query.from_user.id,
                text="❗️ Avval surani tanlang."
            )
            return

        surah_data = get_surah_data(surah_num)
        if not surah_data:
            raise Exception("Sura ma'lumotlari topilmadi")

        total_ayahs = surah_data['numberOfAyahs']

        if ayah_number < 1 or ayah_number > total_ayahs:
            query.answer("⚠️ Bu oyat mavjud emas", show_alert=True)
            return

        ayah = surah_data['ayahs'][ayah_number - 1]

        # Rasm URL
        image_url = f"https://cdn.islamic.network/quran/images/high-resolution/{surah_num}_{ayah_number}.png"
        image_response = requests.get(image_url, timeout=10)

        # Matn tayyorlash
        res_sajda = " emas‼️" if str(ayah['sajda']) == 'False' else "‼️"
        caption = (
            f"<code>🔹{surah_data['englishName']} - surasi [ {ayah_number} | {total_ayahs} ]\n"
            f"🔹Surada: {ayah_number} - oyat\n"
            f"🔹Quronda: {ayah['number']} - oyat\n"
            f"🔹Juz: {ayah['juz']}\n"
            f"🔹Sahifa: {ayah['page']}\n"
            f"⚠️ Ushbu oyat Sajda oyati{res_sajda}\n"
            f"🔹Oyat matni 👇\n{ayah['text']}</code>"
        )

        # Tugmalar
        buttons = [
            [
                InlineKeyboardButton("Audio 🎧", callback_data='audio_ayah'),
                InlineKeyboardButton(f"{ayah_number} | {total_ayahs}", callback_data='current_ayah'),
                InlineKeyboardButton("Tarjima 📄", callback_data='translation_ayah')
            ]
        ]

        # Navigatsiya tugmalari
        nav_buttons = []
        if ayah_number > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️", callback_data='previous_ayah'))
        if ayah_number < total_ayahs:
            nav_buttons.append(InlineKeyboardButton("➡️", callback_data='next_ayah'))
        if nav_buttons:
            buttons.append(nav_buttons)

        # Asosiy tugmalar
        buttons.append([
            InlineKeyboardButton("⬅️ Sura", callback_data=f'back_to_{surah_num}'),
            InlineKeyboardButton("📖 Suralar", callback_data='show_surahs_list')  # O'zgardi
        ])

        markup = InlineKeyboardMarkup(buttons)

        # Xabar yuborish/yangilash
        try:
            if image_response.status_code == 200:
                if len(caption) <= 1000:
                    query.edit_message_media(
                        media=InputMediaPhoto(
                            media=image_response.content,
                            caption=caption,
                            parse_mode="HTML"
                        ),
                        reply_markup=markup
                    )
                else:
                    # Uzun matn uchun
                    query.edit_message_media(
                        media=InputMediaPhoto(
                            media=image_response.content,
                            caption=caption[:1000],
                            parse_mode="HTML"
                        ), reply_markup=markup
                    )
                    context.bot.send_message(
                        chat_id=query.from_user.id,
                        text=caption[1000:],
                        reply_markup=markup,
                        parse_mode="HTML"
                    )
            else:
                query.edit_message_text(
                    text=caption,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Xabarni yangilashda xato: {e}")
            context.bot.send_photo(
                chat_id=query.from_user.id,
                photo=image_response.content if image_response.status_code == 200 else None,
                caption=caption,
                reply_markup=markup,
                parse_mode="HTML"
            )

        # Ma'lumotlarni saqlash
        datas['current_ayah'] = ayah_number
        datas['current_surah'] = surah_num
        datas['translation_ayah'] = ayah['number']

    except Exception as e:
        logger.error(f"show_ayah xatosi: {e}")
        query.answer("⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.", show_alert=True)


def navigate_ayahs(query, context, direction):
    """Oyatlar orasida harakatlanish"""
    try:
        query.answer()
        datas = context.user_data
        current_ayah = datas.get('current_ayah', 1)

        if direction == 'next_ayah':
            new_ayah = current_ayah + 1
        else:
            new_ayah = current_ayah - 1

        show_ayah(query, context, new_ayah)

    except Exception as e:
        logger.error(f"navigate_ayahs xatosi: {e}")
        query.answer("⚠️ Harakatlanishda xatolik yuz berdi.", show_alert=True)


def play_surah_audio(query, context):
    """To‘liq sura audiosini @Quran_By_Ayah Telegram kanalidan yuborish"""
    try:
        query.answer("🎧 Sura audiosi yuborilmoqda...")

        datas = context.user_data
        surah_num = datas.get('current_surah') or datas.get('surah_pages_sec')
        a=int(surah_num)+2

        if not surah_num:
            query.answer("❗️ Avval surani tanlang.", show_alert=True)
            return

        # Havolani yasash
        audio_url = f"https://t.me/Quran_By_Ayah/{a}"

        caption = f"🎧 <b>{a-2}-sura</b> - to‘liq sura audiosi\n@QuranUzBot"

        # Avvalgi xabarni yangilashga harakat qilamiz
        try:
            query.edit_message_media(
                media=InputMediaAudio(
                    media=audio_url,
                    caption=caption,
                    parse_mode="HTML",),
                reply_markup=surah_ikb2()
            )
        except Exception as edit_err:
            logger.warning(f"edit_message_media ishlamadi: {edit_err}")
            # Yangilay olmasa, yangi audio yuboriladi
            context.bot.send_audio(
                chat_id=query.from_user.id,
                audio=audio_url,

                caption=caption,
                parse_mode="HTML",
                title=f"{a}-sura",
                performer="Qori",
                reply_markup=surah_ikb2()
            )

    except Exception as e:
        logger.error(f"play_surah_audio_from_channel xatosi: {e}")
        query.answer("⚠️ Audio yuborishda xatolik yuz berdi.", show_alert=True)


def play_ayah_audio(query, context):
    """Oyat audiosini yuborish"""
    try:
        datas = context.user_data
        surah_num = datas.get('surah_pages_sec')
        query.answer("🎧 Audio yuborilmoqda...")
        datas = context.user_data
        current_ayah = datas.get('current_ayah', 1)
        current_surah = datas.get('current_surah', 1)

        response = requests.get(
            url=f"{QURAN_API}/ayah/{current_surah}:{current_ayah}/ar.alafasy",
            timeout=10
        )
        response.raise_for_status()
        json_data = response.json()

        audio_url = json_data.get("data", {}).get("audio")
        if audio_url:
            context.bot.send_audio(
                chat_id=query.from_user.id,
                audio=audio_url,
                caption=f"🎧 {current_surah}:{current_ayah} oyati audio\n<a href='https://t.me/R_Yusuf_Bot'>@QuranUzBot</a>",
                parse_mode="HTML",
                title=f"Sura {current_surah}, Oyat {current_ayah}",
                performer="Mishary Rashid Alafasy"
            )
        else:
            query.answer("⚠️ Audio topilmadi.", show_alert=True)
    except Exception as e:
        logger.error(f"play_ayah_audio xatosi: {e}")
        query.answer("⚠️ Audio yuborishda xatolik yuz berdi.", show_alert=True)

