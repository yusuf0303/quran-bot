import os
import requests
from deep_translator import GoogleTranslator


from Suralar.API_lar import QURAN_API
from Suralar.menu_button import logger
from Suralar.surah_ikb import surah_ikb

def show_surah_details(query, context):
    try:


        num = query.data.split('_')[-1]

        req = requests.get(f"{QURAN_API}/surah/{num}").json()
        data = req.get('data', {})


        # Tarjima qilish
        translator = GoogleTranslator(source='en', target='uz')
        trans_name = translator.translate(data.get('englishNameTranslation', ''))

        # Formatlash
        caption = (
            f"<b>📖 Sura tafsilotlari</b>\n\n"
            f"<code>🔹 Sura raqami: <b>{data['number']}</b>\n"
            f"🔹 Nomlari: <b>{data['englishName']} ({data['name']})</b>\n"
            f"🔹 Tarjimasi: <b>{trans_name}</b>\n"
            f"🔹 Vahiy turi: <b>{data['revelationType']}</b>\n"
            f"🔹 Oyatlar soni: <b>{data['numberOfAyahs']}</b></code>\n\n"
           f"📢 <a href='https://t.me/KalomUz_News'>Telegram</a> | "
    f"🛠 <a href='https://t.me/KalomUzSupportBot'>Support</a> | "
    f"📸 <a href='https://www.instagram.com/kalomuz/?utm_source=ig_web_button_share_sheet'>Instagram</a>"
)


        context.user_data['current_surah'] = int(num)
        image_path = "images/ayah.jpg"

        try:
            query.delete_message()
        except:
            pass

        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo_file:
                context.bot.send_photo(
                    chat_id=query.from_user.id,
                    photo=photo_file,
                    caption=caption,
                    reply_markup=surah_ikb(),
                    parse_mode="HTML"
                )
        else:
            context.bot.send_message(
                chat_id=query.from_user.id,
                text=caption,
                reply_markup=surah_ikb(),
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"show_surah_details xatosi: {e}")
        try:
            query.answer("⚠️ Sura ma'lumotlarini yuklab bo'lmadi")
        except:
            context.bot.send_message(
                chat_id=query.from_user.id,
                text="⚠️ Sura ma'lumotlarini ko'rsatishda xatolik yuz berdi."
            )