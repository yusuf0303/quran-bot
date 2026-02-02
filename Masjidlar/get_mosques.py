# -*- coding: utf-8 -*-
import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (CallbackContext, CommandHandler, MessageHandler,
                          Filters, ConversationHandler)

from Suralar.menu_button import main_buttons, logger
from Masjidlar.transliterate import to_latin


# ==== States ====
PROVINCE, DISTRICT, MOSQUE = range(3)

# ==== Viloyatlar lug'ati ====
provinces_dict = {
    1: "Тошкент шаһри",
    2: "Тошкент вилояти",
    3: "Андижон вилояти",
    4: "Бухоро вилояти",
    5: "Самарқанд вилояти",
    6: "Сирдарё вилояти",
    7: "Фарғона вилояти",
    8: "Хоразм вилояти",
    9: "Жиззах вилояти",
    10: "Қашқадарё вилояти",
    11: "Навоий вилояти",
    12: "Наманган вилояти",
    13: "Сурхондарё вилояти",
    14: "Қорақалпоғистон"
}


# ==== API funksiyalar ====
def get_province_districts(province_id):
    try:
        res = requests.get(f"https://api.masjid.uz/api/v1/provinces/{province_id}/districts")
        return res.json()
    except:
        return []


def get_provinces():
    try:
        response = requests.get("https://api.masjid.uz/api/v1/provinces")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Viloyatlar ro'yxatini olishda xatolik: {e}")
        return []


def get_mosques_by_districts(district_id):
    try:
        res = requests.get(f"https://api.masjid.uz/api/v1/districts/{district_id}/mosques")
        return res.json()
    except:
        return []


def get_nearest_mosques(lat, lon):
    try:
        res = requests.get(f"https://api.masjid.uz/api/v1/mosques/nearest?lat={lat}&lon={lon}")
        return res.json()
    except:
        return []


# ==== 1. Viloyat menyusi ====
def mosques_menu(update: Update, context: CallbackContext):
    buttons, row = [], []
    for name in provinces_dict.values():
        row.append(KeyboardButton(to_latin(name)))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton("Menyuga qaytish 🔝")])
    update.message.reply_text("Viloyatni tanlang:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return PROVINCE


# ==== 2. Tuman ro'yxati ====
def show_districts(update: Update, context: CallbackContext):
    selected_name = update.message.text.strip()
    province_id = next((pid for pid, name in provinces_dict.items() if to_latin(name) == selected_name), None)
    if not province_id:
        update.message.reply_text("❗ Tanlangan viloyat topilmadi.")
        return PROVINCE
    context.user_data['selected_province_id'] = province_id
    districts = get_province_districts(province_id)
    if not districts:
        update.message.reply_text("❗ Tumanlar topilmadi.")
        return PROVINCE
    buttons, row = [], []
    for d in districts:
        row.append(KeyboardButton(to_latin(d["name"])))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton("⬅️ Orqaga"), KeyboardButton("Menyuga qaytish 🔝")])
    update.message.reply_text(f"📍 {to_latin(selected_name)} tumanlari:",
                              reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return DISTRICT


# ==== 3. Masjidlar ro'yxati ====
def show_mosques(update: Update, context: CallbackContext):
    selected_district = update.message.text.strip()
    province_id = context.user_data.get("selected_province_id")
    districts = get_province_districts(province_id)
    district = next((d for d in districts if to_latin(d["name"]) == selected_district), None)
    if not district:
        update.message.reply_text("❗ Tuman topilmadi.")
        return DISTRICT
    district_id = district["id"]
    context.user_data["selected_district_id"] = district_id
    mosques = get_mosques_by_districts(district_id)
    if not mosques:
        update.message.reply_text("❗ Masjidlar topilmadi.")
        return DISTRICT
    buttons, row = [], []
    for m in mosques:
        row.append(KeyboardButton(to_latin(m["name"])))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton("⬅️ Orqaga"), KeyboardButton("Menyuga qaytish 🔝")])
    update.message.reply_text(f"🕌 {to_latin(selected_district)} tumanidagi masjidlar:",
                              reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return MOSQUE


# ==== 4. Masjid haqida info ====
def show_mosque_info(update: Update, context: CallbackContext):
    name = update.message.text.strip()
    district_id = context.user_data.get("selected_district_id")
    mosques = get_mosques_by_districts(district_id)
    mosque = next((m for m in mosques if to_latin(m["name"]) == name), None)

    if not mosque:
        update.message.reply_text("❗ Masjid topilmadi.")
        return MOSQUE

    lat = mosque.get("latitude")
    lon = mosque.get("longitude")

    # Manzilni yasash
    try:
        districts = get_province_districts(mosque["provinceId"])  # tumanlar ro'yxati
        district_name = next((d["name"] for d in districts if d["id"] == mosque["districtId"]), "Noma'lum tuman")

        provinces = get_provinces()
        province_name = next((p["name"] for p in provinces if p["id"] == mosque["provinceId"]), "Noma'lum viloyat")

        address = f"{province_name}, {district_name}"
    except Exception as e:
        address = "Manzil aniqlanmadi"
        logger.error(f"Manzil aniqlashda xato: {e}")

    # Lokatsiya yuborish
    if lat and lon:
        context.bot.send_location(chat_id=update.effective_chat.id, latitude=lat, longitude=lon)

    # Xabar
    update.message.reply_text(f"🏙 {to_latin(mosque['name'])}\n📍 Manzil: {to_latin(address)}")
    return MOSQUE


# ==== 5. Lokatsiya asosida eng yaqin masjid ====
def get_province_name(province_id):
    try:
        response = requests.get("https://api.masjid.uz/api/v1/provinces")
        provinces = response.json()
        for p in provinces:
            if p['id'] == province_id:
                return p['name']
    except:
        pass
    return ""


def get_district_name(province_id, district_id):
    try:
        response = requests.get(f"https://api.masjid.uz/api/v1/provinces/{province_id}/districts")
        districts = response.json()
        for d in districts:
            if d['id'] == district_id:
                return d['name']
    except:
        pass
    return ""


def handle_location(update: Update, context: CallbackContext):
    print("Location handler is working")
    location = update.message.location
    lat, lon = location.latitude, location.longitude
    nearest = get_nearest_mosques(lat, lon)
    if not nearest:
        update.message.reply_text("❗ Eng yaqin masjid topilmadi. Iltimos, joylashuvni tekshirib qayta jo'nating!")
        return
    mosque = nearest[0]
    name = mosque.get("name", "")
    province_id = mosque.get('provinceId')
    district_id = mosque.get('districtId')

    province = get_province_name(province_id)
    district = get_district_name(province_id, district_id)

    address = f"{province}, {district}"
    lat = mosque.get("latitude")
    lon = mosque.get("longitude")
    distance = float(mosque.get("distance", 0))

    if distance < 1:
        dist_text = f"{int(distance * 1000)} metr"
    else:
        dist_text = f"{round(distance, 3)} km"

    caption = (f"🕌 {to_latin(name)}\n"
               f"📍 Manzil: {to_latin(address)}\n"
               f"📏 Masofa: {dist_text}")
    if lat and lon:
        context.bot.send_location(chat_id=update.effective_chat.id, latitude=lat, longitude=lon)
    update.message.reply_text(caption)


# ==== 6. Orqaga qaytish ====
def back_to_districts(update: Update, context: CallbackContext):
    province_id = context.user_data.get("selected_province_id")
    if not province_id:
        update.message.reply_text("❗ Avval viloyat tanlang.")
        return PROVINCE

    province_name = provinces_dict.get(province_id, "Tanlangan viloyat")
    districts = get_province_districts(province_id)

    if not districts:
        update.message.reply_text("❗ Tumanlar topilmadi.")
        return PROVINCE

    buttons, row = [], []
    for d in districts:
        row.append(KeyboardButton(to_latin(d["name"])))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([KeyboardButton("⬅️ Orqaga"), KeyboardButton("Menyuga qaytish 🔝")])

    update.message.reply_text(
        f"📍 {province_name} tumanlari:",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )

    return DISTRICT


def go_home(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "🏠 Asosiy menyuga qaytdingiz! Quyidagi menyulardan birini tanlang:",
        reply_markup=main_buttons(update.effective_user.id)
    )
    return ConversationHandler.END


# ==== 7. Handler registratsiyasi ====
def setup_mosque_handlers(dp):
    dp.add_handler(MessageHandler(Filters.location, handle_location))
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex("^Masjidlar 🕌$"), mosques_menu)],
        states={
            PROVINCE: [
                MessageHandler(Filters.regex("^Menyuga qaytish 🔝$"), go_home),
                MessageHandler(Filters.text & ~Filters.command, show_districts)
            ],
            DISTRICT: [
                MessageHandler(Filters.regex("^⬅️ Orqaga$"), mosques_menu),
                MessageHandler(Filters.regex("^Menyuga qaytish 🔝$"), go_home),
                MessageHandler(Filters.text & ~Filters.command, show_mosques)
            ],
            MOSQUE: [
                MessageHandler(Filters.regex("^⬅️ Orqaga$"), back_to_districts),
                MessageHandler(Filters.regex("^Menyuga qaytish 🔝$"), go_home),
                MessageHandler(Filters.text & ~Filters.command, show_mosque_info)
            ]
        },
        fallbacks=[CommandHandler("start", go_home)]
    )
    dp.add_handler(conv_handler)


