import os

from Suralar.API_lar import TRANSLATION_API, QURAN_API
from Suralar.menu_button import logger
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def show_translation(query, context):
    """Oyat tarjimasini to'liq ko'rsatish (oldingi va keyingi oyatlar bilan)"""
    try:
        query.answer("Tarjima yuborilmoqda...")

        user_data = context.user_data
        # current_ayah = user_data.get('current_ayah', 1)
        # current_surah = user_data.get('current_surah', 1)
        # translation_ayah = user_data.get('translation_ayah', current_ayah)

        # 1. Surani olish
        surah_num = int(user_data.get('current_surah', 1))

        # 2. Oyat raqamini aniqlash
        if query.data.startswith("next_translation"):
            translation_ayah = user_data.get('translation_ayah', 1) + 1
        elif query.data.startswith("prev_translation"):
            translation_ayah = max(1, user_data.get('translation_ayah', 1) - 1)
        elif query.data.startswith("matn"):
            try:
                _, sura, oyat = query.data.split("|")
                surah_num = int(sura)
                translation_ayah = int(oyat)
            except Exception as e:
                logger.error(f"Matn tugmasi parsing xatoligi: {e}")
                query.answer("❗️ Oyat ma'lumotini olishda xatolik.", show_alert=True)
                return
        else:
            translation_ayah = 1

        user_data['translation_ayah'] = translation_ayah

        # 3. API dan tarjimani olish
        url = TRANSLATION_API
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 4. To'g'ri oyatni topish
        ayah = next(
            (item for item in data.get('quran', [])
             if item.get('chapter') == surah_num and item.get('verse') == translation_ayah),
            None
        )

        if not ayah:
            logger.warning(f"Tarjima topilmadi: surah={surah_num}, ayah={translation_ayah}")
            query.answer("⚠️ Ushbu oyat tarjimasi topilmadi")
            return

        # 5. Xabar matnini tayyorlash
        trans = ayah.get('text', '❗️ Matn mavjud emas.')
        text = (
            f"📖 <b>{surah_num}-sura, {translation_ayah}-oyat tarjimasi</b>\n\n"
            f"<code>{trans}</code>\n\n"
            
            f"🛠 <a href='https://t.me/KalomUzSupportBot'>Support</a> | "
            f"📸 <a href='https://www.instagram.com/kalomuz/?utm_source=ig_web_button_share_sheet'>Instagram</a>"

        )

        # 6. Tugmalar paneli
        buttons = [
            [
                InlineKeyboardButton("Do'stlarga ulashish ⤴️",
                                     switch_inline_query=f"Quron tarjimasi: {trans[:50]}...")
            ],
            [
                InlineKeyboardButton("⏪ Oldingi", callback_data="prev_translation"),
                InlineKeyboardButton("⏩ Keyingi", callback_data="next_translation")
            ],
            [
                InlineKeyboardButton("📜 Suraga qaytish", callback_data=f"back_to_{surah_num}")
            ]
        ]

        # 7. Avvalgi xabarni o'chirish
        try:
            last_msg_id = user_data.get('last_message_id')
            if last_msg_id:
                context.bot.delete_message(chat_id=query.from_user.id, message_id=last_msg_id)
        except Exception as e:
            logger.warning(f"Xabarni o'chirishda xato: {e}")

        # 8. Yangi xabar yuborish
        msg = context.bot.send_message(
            chat_id=query.from_user.id,
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )

        # 9. Xabar ID sini saqlash
        user_data['last_message_id'] = msg.message_id

    except requests.exceptions.Timeout:
        logger.error("Tarjima API javob bermadi (timeout)")
        query.answer("⏱ Serverdan javob olinmadi. Iltimos, keyinroq urinib ko'ring.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Tarjima API so'rovida xato: {e}")
        query.answer("⚠️ Tarjima serverida xatolik yuz berdi.")
    except Exception as e:
        logger.error(f"Tarjima ko'rsatishda xato: {e}")
        query.answer("⚠️ Xatolik yuz berdi. Iltimos, qayta urunib ko'ring.")

def show_ayah_list(query, context):
    """Suraga tegishli oyatlar ro'yxatini ko'rsatish"""
    try:
        query.answer("Oyatlar ro'yxati yuborilmoqda...")

        datas = context.user_data
        surah = datas.get('surah_pages_sec')
        current_page = datas.get('ayah_page')

        # Get surah info
        response = requests.get(f"{QURAN_API}/surah/{surah}", timeout=10)
        response.raise_for_status()
        surah_data = response.json().get('data', {})
        total_ayahs = surah_data.get('numberOfAyahs', 0)
        surah_name = surah_data.get('name', '')

        if total_ayahs == 0:
            raise Exception("Oyatlar topilmadi.")

        # Calculate pagination
        max_per_page = 48
        start_index = current_page * max_per_page
        end_index = min(start_index + max_per_page, total_ayahs)

        buttons = [
            InlineKeyboardButton(text=str(i + 1), callback_data=f"ayah_{surah}_{i + 1}")
            for i in range(start_index, end_index)
        ]

        # Arrange buttons in rows of 8
        ayah_btns = [buttons[i:i + 8] for i in range(0, len(buttons), 8)]

        # Navigation buttons
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Orqaga", callback_data="prev_ayah_page"))
        if end_index < total_ayahs:
            nav_buttons.append(InlineKeyboardButton("Keyingi ➡️", callback_data="next_page_ayahs"))

        if nav_buttons:
            ayah_btns.append(nav_buttons)

        # Constant buttons
        back_btn = InlineKeyboardButton("⬅️ Sura", callback_data=f'back_to_{surah_data["number"]}')
        home_btn = InlineKeyboardButton("📖 Suralar", callback_data='list_surahs')
        ayah_btns.append([back_btn, home_btn])

        reply_markup = InlineKeyboardMarkup(ayah_btns)
        caption = f"📜 {surah_name} surasi oyatlari ({start_index + 1}-{end_index}/{total_ayahs}) 👇"

        # Try to delete previous message if exists
        try:
            query.delete_message()
        except:
            pass

        # Send new message
        photo_path = "images/Ayahs.png"
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                context.bot.send_photo(
                    chat_id=query.from_user.id,
                    photo=photo,
                    caption=caption,
                    reply_markup=reply_markup
                )
        else:
            context.bot.send_message(
                chat_id=query.from_user.id,
                text=caption,
                reply_markup=reply_markup
            )

    except Exception as e:
        logger.error(f"show_ayah_list xatosi: {e}")
        try:
            query.edit_message_text("⚠️ Oyatlar ro'yxatini yuklashda xatolik yuz berdi.")
        except:
            context.bot.send_message(
                chat_id=query.from_user.id,
                text="⚠️ Oyatlar ro'yxatini yuklashda xatolik yuz berdi."
            )