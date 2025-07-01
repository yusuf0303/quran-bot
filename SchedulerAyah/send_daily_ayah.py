import random
import requests
from datetime import datetime
from telegram import Bot
from Suralarni_toping.surahs import SURAH_NAMES
from Suralarni_toping.database import get_all_user_ids  # siz yaratgan funksiya bo'lishi kerak

TRANSLATION_API = "https://api.alquran.cloud/v1/quran/uz.sodik"
QURAN_API = "https://api.alquran.cloud/v1"


def send_daily_random_ayah_to_all_users(bot: Bot):
    """Har kuni random oyatni barcha foydalanuvchilarga yuborish"""
    now = datetime.now().time()
    if not (6 <= now.hour <= 20):
        return  # faqat bomdoddan xuftongacha

    # 1. Random oyat tanlash
    sura = random.choice(SURAH_NAMES)
    sura_num = sura['number']
    max_oyat = sura['count']
    oyat_num = random.randint(1, max_oyat)

    # 2. API so‘rovlari
    res_arab = requests.get(f"{QURAN_API}/ayah/{sura_num}:{oyat_num}/ar.alafasy").json()
    res_trans = requests.get(TRANSLATION_API).json()

    arab_matn = res_arab['data']['text']
    audio_url = res_arab['data'].get('audio')
    rasm_url = f"https://cdn.islamic.network/quran/images/high-resolution/{sura_num}_{oyat_num}.png"

    tarjima_oyat = next(
        (a for a in res_trans['data']['ayahs']
         if a['surah']['number'] == sura_num and a['numberInSurah'] == oyat_num),
        None
    )
    tarjima = tarjima_oyat['text'] if tarjima_oyat else "Tarjima topilmadi"

    # 3. Foydalanuvchilarga yuborish
    caption_matn = (
        f"📖 <b>{sura_num}-sura, {oyat_num}-oyat</b>\n\n"
        f"<code>{arab_matn}</code>"
    )
    caption_tarjima = f"📘 <code>{tarjima}</code>"

    user_ids = get_all_user_ids()

    for user_id in user_ids:
        try:
            bot.send_photo(
                chat_id=user_id,
                photo=rasm_url,
                caption=caption_matn,
                parse_mode="HTML"
            )
            if audio_url:
                bot.send_audio(
                    chat_id=user_id,
                    audio=audio_url,
                    caption=caption_tarjima,
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Xatolik foydalanuvchiga ({user_id}) yuborishda: {e}")
