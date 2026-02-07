import logging

import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, MessageHandler, Filters,
    CallbackContext, ConversationHandler
)
from datetime import datetime

from Suralar.menu_button import main_buttons, logger
from namoz_vaqtlari.get_regeions import DISTRICTS, REGIONS, API_REGION_NAMES

REGION, DISTRICT, PRAYER_TIME = range(3)


PRAYER_TIMES = [
    ["Bomdod 🌅", "Peshin 🕑", "Asr 🌇"],
    ["Shom 🌆", "Xufton 🌃"],
    ["Bugun (To'liq) 📅", "Shu hafta (To'liq) 🗓️"],
    ["⬅️ Orqaga", "Menyuga qaytish 🔝"]
]

FOOTER_LINKS = ("""
📢 <a href='https://t.me/KalomUz_News'>Telegram</a>|
🛠 <a href='https://t.me/KalomUzSupportBot'>Support</a> |  
📸 <a href='https://www.instagram.com/kalomuz/?utm_source=ig_web_button_share_sheet'>Instagram</a>

"""
                )

REGION_EMOJIS = {
    "Toshkent": "🏙",
    "Andijon": "⛰",
    "Farg'ona": "🌄",
    "Namangan": "🏞",
    "Samarqand": "🏛",
    "Buxoro": "🕌",
    "Navoiy": "🏭",
    "Xorazm": "🏺",
    "Qashqadaryo": "🏜",
    "Surxondaryo": "🌅",
    "Jizzax": "🌾",
    "Sirdaryo": "🌊",
    "Nukus (Qoraqalpog'iston Res)": "🏕"
}


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "🕌 Assalomu alaykum! KalomUz botiga xush kelibsiz!\n\n"
        "Quyidagi menyulardan birini tanlang:",
        reply_markup=main_buttons(update.effective_user.id)
    )
    return ConversationHandler.END


def prayer_times_menu(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text="📌 Viloyatlardan birini tanlang:",
        reply_markup=ReplyKeyboardMarkup(REGIONS, resize_keyboard=True)
    )
    return REGION


def get_region(update: Update, context: CallbackContext) -> int:
    region = update.message.text
    if "Nukus" in region:
        region = "Nukus (Qoraqalpog'iston Res)"

    context.user_data["region"] = region

    # Prepare district buttons
    districts = DISTRICTS.get(region, [f"{region} shahar"])
    district_buttons = [districts[i:i + 3] for i in range(0, len(districts), 3)]
    district_buttons.append(["⬅️ Orqaga", "Menyuga qaytish 🔝"])

    emoji = REGION_EMOJIS.get(region, "📍")
    update.message.reply_text(
        f"{emoji} <b>{region} viloyati uchun tuman/shaharni tanlang:</b>",
        reply_markup=ReplyKeyboardMarkup(district_buttons, resize_keyboard=True),
        parse_mode="HTML"
    )
    return DISTRICT


def get_district(update: Update, context: CallbackContext) -> int:
    district = update.message.text
    region = context.user_data.get("region", "Toshkent")

    if district == "⬅️ Orqaga":
        return back_to_regions(update, context)
    elif district == "Menyuga qaytish 🔝":
        return go_home(update, context)

    context.user_data["district"] = district
    emoji = REGION_EMOJIS.get(region, "🕌")

    update.message.reply_text(
        f"{emoji} <b><i>{region} viloyati, {district} uchun namoz vaqtlari</i></b>\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=ReplyKeyboardMarkup(PRAYER_TIMES, resize_keyboard=True),
        parse_mode="HTML"
    )
    return PRAYER_TIME


def format_prayer_time(update: Update, context: CallbackContext, prayer_key: str, prayer_name: str, emoji: str):
    try:
        region = context.user_data.get("region", "Toshkent")
        district = context.user_data.get("district", None)
        data = get_data(region, district)

        if not data or 'times' not in data or prayer_key not in data['times']:
            update.message.reply_text(
                f"❗️ {prayer_name} vaqti hozircha mavjud emas. Iltimos, birozdan so‘ng qayta urinib ko‘ring."
            )
            return

        location = f"{district}, {region}" if district else region
        region_emoji = REGION_EMOJIS.get(region, "🕌")

        text = (
            f"{emoji} <b>{prayer_name} vaqti</b>\n\n"
            f"{region_emoji} <b>Hudud:</b> {location}\n"
            f"📅 <b>Sana:</b> {data.get('date', 'Noma’lum')} ({data.get('weekday', '-')})\n\n"
            f"⏰ <b>Vaqt:</b> <code>{data['times'][prayer_key]}</code>\n\n"
            # f"{get_time_remaining(data['times'][prayer_key])}"
            f"{FOOTER_LINKS}"
        )

        update.message.reply_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Ulashish", switch_inline_query=f"namoz_{region}_{district if district else ''}")]
            ])
        )
        # Also show the navigation menu if it's not there, but it should be already

    except Exception as e:
        logging.error(f"{prayer_name} vaqtini olishda xatolik: {e}")
        update.message.reply_text(
            f"⚠️ {prayer_name} vaqtini yuklab bo‘lmadi.\n"
            f"Iltimos, internet aloqasini tekshiring yoki birozdan so‘ng qayta urinib ko‘ring."
        )


# def get_time_remaining(prayer_time: str) -> str:
#     from datetime import datetime
#     fmt = "%H:%M"
#     now = datetime.now()
#     try:
#         target_time = datetime.strptime(prayer_time, fmt).replace(
#             year=now.year, month=now.month, day=now.day)
#         if now > target_time:
#             return "🕰 Bu namoz vaqti o'tib bo'ldi\n\n"
#
#         delta = target_time - now
#         hours, remainder = divmod(int(delta.total_seconds()), 3600)
#         minutes = remainder // 60
#         return f"⌛ Qolgan vaqt: <b>{hours} soat {minutes} daqiqa</b>\n\n"
#     except Exception as e:
#         return ""

def format_daily_prayers(update: Update, context: CallbackContext):
    try:
        region = context.user_data.get("region", "Toshkent")
        district = context.user_data.get("district", None)
        data = get_data(region, district)

        if not data or not data.get("times"):  # Agar ma'lumot yo'q bo‘lsa
            update.message.reply_text(
                "❗️Bugungi namoz vaqtlari yuklab olinmadi.\n"
                "Iltimos, internet aloqasini tekshiring yoki birozdan so‘ng qayta urinib ko‘ring."
            )
            return

        location = f"{district}, {region}" if district else region
        region_emoji = REGION_EMOJIS.get(region, "🕌")
        today = datetime.now().strftime("%d.%m.%Y")

        prayers = [
            {"key": "tong_saharlik", "name": "Bomdod (Saharlik)", "emoji": "🌄"},
            {"key": "quyosh", "name": "Quyosh", "emoji": "☀️"},
            {"key": "peshin", "name": "Peshin", "emoji": "🕑"},
            {"key": "asr", "name": "Asr", "emoji": "🌇"},
            {"key": "shom_iftor", "name": "Shom (Iftor)", "emoji": "🌆"},
            {"key": "hufton", "name": "Xufton", "emoji": "🌃"}
        ]

        text = (
            f"<b>📍 {district.title()} tumani uchun namoz vaqtlari:</b>\n"
            f"<i>🗓 {data['date']} ({data['weekday']})</i>\n\n"
            f"<b>🌅 Bomdod (Saharlik):</b> {data['times']['tong_saharlik']}\n"
            f"<b>🌞 Quyosh:</b> {data['times']['quyosh']}\n"
            f"<b>🕑 Peshin:</b> {data['times']['peshin']}\n"
            f"<b>🌇 Asr:</b> {data['times']['asr']}\n"
            f"<b>🌆 Shom (Iftor):</b> {data['times']['shom_iftor']}\n"
            f"<b>🌃 Xufton:</b> {data['times']['hufton']}\n"
            f"{FOOTER_LINKS}"
        )

        update.message.reply_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Ulashish", switch_inline_query=f"namoz_{region}_{district if district else ''}")]
            ])
        )

    except Exception as e:
        logging.error(f"format_daily_prayers xatolik: {e}")
        update.message.reply_text(
            "⚠️ Namoz vaqtlari ma'lumotlarini yuklab olishda xatolik yuz berdi.\n"
            "Iltimos, birozdan so‘ng qayta urinib ko‘ring."
        )


def format_weekly_prayers(update: Update, context: CallbackContext):
    try:
        region = context.user_data.get("region", "Toshkent")
        district = context.user_data.get("district", None)
        url = f"https://islomapi.uz/api/present/week?region={region}"

        response = requests.get(url, timeout=20)
        if response.status_code != 200:
            raise Exception(f"Status code: {response.status_code}")

        week_data = response.json()
        if not week_data or not isinstance(week_data, list):
            update.message.reply_text(
                "❗️Haftalik namoz vaqtlari hozircha mavjud emas. Iltimos, birozdan so‘ng qayta urinib ko‘ring."
            )
            return

        location = f"{district}, {region}" if district else region
        region_emoji = REGION_EMOJIS.get(region, "🕌")
        today = datetime.now().strftime("%d.%m.%Y")

        text = (
            f"📅 <b>{location} uchun haftalik namoz vaqtlari</b>\n"
            f"{region_emoji} <b>Viloyat:</b> {region}\n"
            f"🗓 <b>Joriy sana:</b> {today}\n\n"
        )

        for day in week_data:
            times = day.get("times", {})
            text += (
                f"───────\n"
                f"📌 <b>{day.get('date', 'Sana mavjud emas')} ({day.get('weekday', '-')})</b>\n"
                f"🌄 Bomdod: <code>{times.get('tong_saharlik', '-')}</code>\n"
                f"🕑 Peshin: <code>{times.get('peshin', '-')}</code>\n"
                f"🌇 Asr: <code>{times.get('asr', '-')}</code>\n"
                f"🌆 Shom: <code>{times.get('shom_iftor', '-')}</code>\n"
                f"🌃 Xufton: <code>{times.get('hufton', '-')}</code>\n"
            )

        text += f"\n{FOOTER_LINKS}"

        update.message.reply_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 Ulashish", switch_inline_query=f"namoz_{region}_{district if district else ''}")]
            ])
        )

    except Exception as e:
        logging.error(f"format_weekly_prayers xatolik: {e}")
        update.message.reply_text(
            "⚠️ Haftalik namoz vaqtlari yuklab olinmadi.\n"
            "Iltimos, internet aloqasini tekshiring yoki birozdan so‘ng qayta urinib ko‘ring."
        )


def back_to_regions(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text="📌 Viloyatlardan birini tanlang:",
        reply_markup=ReplyKeyboardMarkup(REGIONS, resize_keyboard=True)
    )
    return REGION


def back_to_districts(update: Update, context: CallbackContext) -> int:
    region = context.user_data.get("region", "Toshkent")
    districts = DISTRICTS.get(region, [f"{region} shahar"])
    district_buttons = [districts[i:i + 3] for i in range(0, len(districts), 3)]
    district_buttons.append(["⬅️ Orqaga", "Menyuga qaytish 🔝"])

    emoji = REGION_EMOJIS.get(region, "📍")
    update.message.reply_text(
        f"{emoji} <b>{region} viloyati uchun tuman/shaharni tanlang:</b>",
        reply_markup=ReplyKeyboardMarkup(district_buttons, resize_keyboard=True),
        parse_mode="HTML"
    )
    return DISTRICT


def go_home(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "🏠 Asosiy menyuga qaytdingiz! Quyidagi menyulardan birini tanlang:",
        reply_markup=main_buttons(update.effective_user.id)
    )
    return ConversationHandler.END


def get_data(region, district=None):
    try:
        # Viloyat nomini API uchun formatga o'tkazamiz
        api_region = API_REGION_NAMES.get(region, region.lower())

        url = f"https://islomapi.uz/api/present/day?region={api_region}"
        response = requests.get(url, timeout=(5, 10))

        if response.status_code == 200:
            data = response.json()
            if data.get('success') is False or 'times' not in data:
                logger.warning(f"islomapi.uz returned error or empty data for {region}. Trying fallback...")
                return get_aladhan_data(region, district)
            return data
        else:
            logger.warning(f"islomapi.uz failed with status {response.status_code}. Trying fallback...")
            return get_aladhan_data(region, district)

    except Exception as e:
        logger.error(f"Error getting data for {region} from islomapi.uz: {str(e)}")
        return get_aladhan_data(region, district)


def get_aladhan_data(region, district=None):
    """Fallback function to get data from aladhan.com"""
    try:
        # Mapping for better city search on Aladhan
        ALADHAN_CITIES = {
            "Toshkent": "Tashkent",
            "Andijon": "Andijan",
            "Farg'ona": "Fergana",
            "Namangan": "Namangan",
            "Samarqand": "Samarkand",
            "Buxoro": "Bukhara",
            "Navoiy": "Navoi",
            "Xorazm": "Urgench",
            "Qashqadaryo": "Qarshi",
            "Surxondaryo": "Termiz",
            "Jizzax": "Jizzakh",
            "Sirdaryo": "Guliston",
            "Nukus (Qoraqalpog'iston Res)": "Nukus"
        }
        
        city = district if district else region
        # If the district name is known to be slightly different or specific, adjust it
        if city in ALADHAN_CITIES:
            city = ALADHAN_CITIES[city]
        elif region in ALADHAN_CITIES:
             pass # Use district as is, but country is Uzbekistan
        
        # Method 3: Muslim World League
        # School 1: Hanafi
        url = f"http://api.aladhan.com/v1/timingsByCity?city={city}&country=Uzbekistan&method=3&school=1"
        response = requests.get(url, timeout=(5, 10))
        
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("code") == 200:
                timings = res_data["data"]["timings"]
                date_info = res_data["data"]["date"]
                
                # Convert to islomapi format
                data = {
                    "region": region,
                    "date": date_info["gregorian"]["date"],
                    "weekday": date_info["gregorian"]["weekday"]["en"], # Aladhan provides English weekdays
                    "times": {
                        "tong_saharlik": timings["Fajr"],
                        "quyosh": timings["Sunrise"],
                        "peshin": timings["Dhuhr"],
                        "asr": timings["Asr"],
                        "shom_iftor": timings["Maghrib"],
                        "hufton": timings["Isha"]
                    }
                }
                
                # Weekday mapping to Uzbek
                WEEKDAY_MAP = {
                    "Monday": "Dushanba",
                    "Tuesday": "Seshanba",
                    "Wednesday": "Chorshanba",
                    "Thursday": "Payshanba",
                    "Friday": "Juma",
                    "Saturday": "Shanba",
                    "Sunday": "Yakshanba"
                }
                data["weekday"] = WEEKDAY_MAP.get(data["weekday"], data["weekday"])
                
                return data
        
        logger.error(f"Aladhan fallback also failed for {city}")
        return None
        
    except Exception as e:
        logger.error(f"Error in aladhan fallback for {region}: {str(e)}")
        return None


def setup_prayer_times_handlers(dp):
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(Filters.regex("^Namoz vaqtlari 🧎‍♂️$"), prayer_times_menu)
        ],
        states={
            REGION: [
                MessageHandler(Filters.regex("^Menyuga qaytish 🔝$"), go_home),
                MessageHandler(Filters.text & ~Filters.command, get_region),
            ],
            DISTRICT: [
                MessageHandler(Filters.regex("^⬅️ Orqaga$"), back_to_regions),
                MessageHandler(Filters.regex("^Menyuga qaytish 🔝$"), go_home),
                MessageHandler(Filters.text & ~Filters.command, get_district),
            ],
            PRAYER_TIME: [
                MessageHandler(Filters.regex("^Bomdod 🌅$"),
                               lambda u, c: format_prayer_time(u, c, "tong_saharlik", "Bomdod (Saharlik)", "🌄")),
                MessageHandler(Filters.regex("^Peshin 🕑$"),
                               lambda u, c: format_prayer_time(u, c, "peshin", "Peshin", "🕑")),
                MessageHandler(Filters.regex("^Asr 🌇$"),
                               lambda u, c: format_prayer_time(u, c, "asr", "Asr", "🌇")),
                MessageHandler(Filters.regex("^Shom 🌆$"),
                               lambda u, c: format_prayer_time(u, c, "shom_iftor", "Shom (Iftor)", "🌆")),
                MessageHandler(Filters.regex("^Xufton 🌃$"),
                               lambda u, c: format_prayer_time(u, c, "hufton", "Xufton", "🌃")),
                MessageHandler(Filters.regex("^Bugun \\(To'liq\\) 📅$"), format_daily_prayers),
                MessageHandler(Filters.regex("^Shu hafta \\(To'liq\\) 🗓️$"), format_weekly_prayers),
                MessageHandler(Filters.regex("^⬅️ Orqaga$"), back_to_districts),
                MessageHandler(Filters.regex("^Menyuga qaytish 🔝$"), go_home),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    dp.add_handler(conv_handler)
