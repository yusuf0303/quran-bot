import random
import requests
import logging
import pytz
from datetime import datetime
from telegram import Bot
from Suralarni_toping.surahs import SURAH_NAMES
from Suralarni_toping.database import get_all_user_ids  # siz yaratgan funksiya bo'lishi kerak

# API endpointlar
TRANSLATION_API = "https://api.alquran.cloud/v1/quran/uz.sodik"
QURAN_API = "https://api.alquran.cloud/v1"

# Kanal username (agar private bo'lsa, -100... shaklidagi ID ni qo'ying)
DEFAULT_CHANNEL = "@KalomUz_News"

# Logging sozlamalari
logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

# Requests session va tarjima cache (bir martalik yuklash uchun)
_session = requests.Session()
_TRANSLATION_CACHE = None


def _load_translation_cache():
    """
    Tarjima API ni bir marta yuklab, keyingi chaqiriqlarda cache dan foydalanish.
    Agar yuklashda xato bo'lsa, None qaytaradi.
    """
    global _TRANSLATION_CACHE
    if _TRANSLATION_CACHE is not None:
        return _TRANSLATION_CACHE

    try:
        logger.info("Tarjima ma'lumotlarini yuklash: %s", TRANSLATION_API)
        resp = _session.get(TRANSLATION_API, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        # Qaytgan formatni tekshirish
        surahs = data.get("data", {}).get("surahs")
        if surahs:
            _TRANSLATION_CACHE = surahs
            logger.info("Tarjima muvaffaqiyatli yuklandi va cache ga saqlandi.")
            return _TRANSLATION_CACHE
        else:
            logger.error("Tarjima API kutilgan formatda javob qaytarmadi.")
    except Exception as e:
        logger.exception("Tarjima API dan yuklashda xatolik: %s", e)

    return None


def _get_translation_text(sura_num: int, oyat_num: int):
    """
    Cache ichidan berilgan sura va oyat uchun tarjimani topadi.
    Topilmasa None qaytaradi.
    """
    surahs = _load_translation_cache()
    if not surahs:
        return None
    try:
        for surah in surahs:
            if surah.get("number") == sura_num:
                ayah = next(
                    (a for a in surah.get("ayahs", []) if a.get("numberInSurah") == oyat_num),
                    None
                )
                if ayah:
                    return ayah.get("text")
    except Exception as e:
        logger.exception("Tarjima cache dan o'qishda xato: %s", e)
    return None


def send_daily_random_ayah_to_all_users(bot: Bot):
    """
    Har kuni random oyatni barcha foydalanuvchilarga va kanalga yuboradi.
    Faqat Asia/Tashkent vaqt zonasidagi 06:00 - 20:00 oralig'ida ishlaydi.
    """
    # Vaqtni Toshkent bo'yicha olish
    try:
        now = datetime.now(pytz.timezone("Asia/Tashkent"))
    except Exception:
        # Agar pytz ishlamasa yoki boshqa xato bo'lsa, fallback UTC
        now = datetime.utcnow()
        logger.warning("pytz bilan vaqt olishda muammo; UTCga fallback qilindi.")

    if not (6 <= now.hour <= 20):
        logger.info("Vaqt oralig'idan tashqarida (Asia/Tashkent): %s — ish bajarilmadi.", now.isoformat())
        return

    # 1) Random sura va oyat tanlash
    sura = random.choice(SURAH_NAMES)
    sura_num = sura["number"]
    suraEngName = sura.get("englishName", sura.get("name", f"Sura {sura_num}"))
    max_oyat = sura["count"]
    oyat_num = random.randint(1, max_oyat)
    logger.info("Tanlandi: %s — %s:%s", suraEngName, sura_num, oyat_num)

    # 2) Arab matn va audio olish (API so'rovi)
    arab_matn = None
    audio_url = None
    try:
        url = f"{QURAN_API}/ayah/{sura_num}:{oyat_num}/ar.alafasy"
        resp = _session.get(url, timeout=15)
        resp.raise_for_status()
        j = resp.json()
        arab_matn = j.get("data", {}).get("text")
        audio_url = j.get("data", {}).get("audio")
        if not arab_matn:
            logger.error("Arab matn API javobida topilmadi: %s", url)
            return
    except Exception as e:
        logger.exception("Arab oyat API so'rovida xatolik: %s", e)
        return

    # 3) Tarjima olish (cache orqali)
    tarjima = None
    try:
        tarjima = _get_translation_text(sura_num, oyat_num)
    except Exception as e:
        logger.exception("Tarjima topishda xatolik: %s", e)
        tarjima = None
    if not tarjima:
        tarjima = "Tarjima topilmadi"

    # 4) URLlar va caption tayyorlash
    rasm_url = f"https://cdn.islamic.network/quran/images/high-resolution/{sura_num}_{oyat_num}.png"
    caption_matn = (
        f"<b>{suraEngName} surasi</b>\n📖  <b>{sura_num}-sura, {oyat_num}-oyat</b>\n\n"
        f"<code>{arab_matn}</code>\n\n@KalomUzBot"
    )
    caption_tarjima = f"📘  <code>{tarjima}</code>\n\n@KalomUzBot"

    # 5) Foydalanuvchilar ro'yxatini olish
    try:
        user_ids = get_all_user_ids() or []
    except Exception as e:
        logger.exception("Foydalanuvchi IDlarini olishda xato: %s", e)
        user_ids = []

    # 6) Foydalanuvchilarga yuborish (har biriga alohida try/except)
    for user_id in user_ids:
        try:
            bot.send_photo(
                chat_id=user_id,
                photo=rasm_url,
                caption=caption_matn,
                parse_mode="HTML"
            )
            logger.info("Rasm yuborildi user: %s", user_id)
        except Exception as e:
            logger.exception("Rasm yuborishda xato user (%s): %s", user_id, e)
            # davom etamiz — bitta foydalanuvchi xatosi butun jobni to'xtatmasin
            continue

        # audio yuborish (agar mavjud bo'lsa)
        if audio_url:
            try:
                bot.send_audio(
                    chat_id=user_id,
                    audio=audio_url,
                    caption=caption_tarjima,
                    parse_mode="HTML"
                )
                logger.info("Audio yuborildi user: %s", user_id)
            except Exception as e:
                logger.exception("Audio yuborishda xato user (%s): %s", user_id, e)
                continue

    # 7) Kanalga yuborish (kanalga ruxsat/adminka kerak)
    try:
        bot.send_photo(
            chat_id=DEFAULT_CHANNEL,
            photo=rasm_url,
            caption=caption_matn,
            parse_mode="HTML"
        )
        logger.info("Rasm yuborildi kanalga: %s", DEFAULT_CHANNEL)
    except Exception as e:
        logger.exception("Rasm yuborishda xato kanalga (%s): %s", DEFAULT_CHANNEL, e)

    if audio_url:
        try:
            bot.send_audio(
                chat_id=DEFAULT_CHANNEL,
                audio=audio_url,
                caption=caption_tarjima,
                parse_mode="HTML"
            )
            logger.info("Audio yuborildi kanalga: %s", DEFAULT_CHANNEL)
        except Exception as e:
            logger.exception("Audio yuborishda xato kanalga (%s): %s", DEFAULT_CHANNEL, e)

