import mysql.connector
import requests
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from deep_translator import GoogleTranslator

from data.config import *
from keyboards.inline.regions import regions_list, day_part, back_btns

from loader import dp, bot
from states.admin import ADMIN
from states.user import USER

db_connection = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    auth_plugin=auth_plugin
)
cursor = db_connection.cursor()


def user_lang(user_id):
    select_query = 'select lang from users_list where user_id=%s'
    select_value = (user_id,)
    cursor.execute(select_query, select_value)
    datas = cursor.fetchall()
    db_connection.commit()
    user_language = datas[0][0]
    return user_language


@dp.message_handler(Text(equals=['Время молитвы 🕌', 'Prayer times 🕌', 'Namoz vaqtlari 🕌']),
                    state=[ADMIN.main_menu, USER.main_menu])
async def prayer_times(message: types.Message):
    user_id = message.from_user.id
    if user_lang(user_id) == 'uzb':
        with open('handlers/images/prayer_times.png', 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=user_id, caption="Namoz vaqtlari",
                                 reply_markup=regions_list(user_id))
    elif user_lang(user_id) == 'eng':
        with open('handlers/images/prayer_times.png', 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=user_id, caption="Prayer times",
                                 reply_markup=regions_list(user_id))
    elif user_lang(user_id) == 'rus':
        with open('handlers/images/prayer_times.png', 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=user_id, caption="Время молитвы",
                                 reply_markup=regions_list(user_id))


@dp.message_handler(Text(equals=['Sozlamalar 🛠', 'Settings 🛠', 'Настройки 🛠']), state=[ADMIN.main_menu, USER.main_menu])
async def settings_menu(message: types.Message):
    user_id = message.from_user.id
    if user_lang(user_id) == 'uzb':
        await message.answer("Sozlamalar")
    elif user_lang(user_id) == 'eng':
        await message.answer("Settings")
    elif user_lang(user_id) == 'rus':
        await message.answer("Настройки 🛠")


@dp.callback_query_handler(state=[ADMIN.main_menu, USER.main_menu])
async def region_list(call: types.CallbackQuery, state: FSMContext):
    callback = call.data
    user_id = call.from_user.id

    regions_rus = {
        "Ташкенте": "Toshkent",
        "Самарканде": "Samarqand",
        "Андижане": "Andijon",
        "Бухаре": "Buxoro",
        "Фергану": "Farg'ona",
        "Гулистан": "Guliston",
        "Джизаке": "Jizzax",
        "Карши": "Qarshi",
        "Намангане": "Namangan",
        "Навои": "Navoiy",
        "Хиву": "Xiva",
        "Нукусе (Каракалпакский Рес)": "Nukus"
    }

    regions_eng = {
        "Ташкенте": "Toshkent",
        "Самарканде": "Samarqand",
        "Андижане": "Andijon",
        "Бухаре": "Buxoro",
        "Фергану": "Farg'ona",
        "Гулистан": "Guliston",
        "Джизаке": "Jizzax",
        "Карши": "Qarshi",
        "Намангане": "Namangan",
        "Навои": "Navoiy",
        "Хиву": "Xiva",
        "Нукусе (Каракалпакский Рес)": "Nukus"
    }

    regions = {'tashkent', 'samarkand', 'andijon', 'buxoro', 'fargona', 'guliston', 'jizzax', 'qarshi', 'namangan',
               'navoiy', 'xiva', 'nukus'}
    if callback in regions:
        await call.answer("Success")
        button_text = None

        reply_markup = call.message.reply_markup
        if reply_markup and isinstance(reply_markup, types.InlineKeyboardMarkup):
            for row in reply_markup.inline_keyboard:
                for button in row:
                    if button.callback_data == callback:
                        button_text = button.text
                        break
                if button_text:
                    break

        caption = f"{button_text} uchun namoz vaqtlari 👇"

        if user_lang(user_id) == 'uzb':
            caption = caption
            org_region = button_text
            await state.update_data({'region': org_region, 'region_callback': callback})
        elif user_lang(user_id) == 'eng':
            org_region = regions_eng[f'{button_text}']
            await state.update_data({'region': org_region, 'region_callback': callback})
            translator = GoogleTranslator(target='en', source='uz')
            caption = translator.translate(caption)
        elif user_lang(user_id) == 'rus':
            org_region = regions_rus[f'{button_text}']
            await state.update_data({'region': org_region, 'region_callback': callback})
            translator = GoogleTranslator(target='ru', source='uz')
            caption = translator.translate(caption)

        media = [types.InputMediaPhoto(media=InputFile(f'handlers/images/{callback}.jpg',
                                                       f'{callback}.jpg'),
                                       caption=caption)]
        await call.message.edit_media(media=media[0], reply_markup=day_part(user_id))
        await USER.region.set()


@dp.callback_query_handler(state=USER.region)
async def day_parts(call: types.CallbackQuery, state: FSMContext):
    callback = call.data
    user_id = call.from_user.id

    datas = await state.get_data()
    region = datas.get('region')

    if callback == 'bomdod':
        req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
        fajr = req['times']['tong_saharlik']
        sunrise = req['times']['quyosh']
        day = req['weekday']
        date = req['date']

        bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
        creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
        caption = (f"<code>{region} - uchun Bomdod namozi vaqti!\n\nHafta kuni: {day}\nSana: {date}\n\n👉 Bomdod ("
                   f"Saharlik): {fajr}\n👉 Quyosh chiqishi: {sunrise}</code>\n\n{bot_link}\n{creator}")

        if user_lang(user_id) == 'uzb':
            caption = caption
            await call.answer("Ma'lumotlar olinmoqda")
        elif user_lang(user_id) == 'eng':
            translator = GoogleTranslator(target='en', source='uz')
            caption = translator.translate(caption)
            await call.answer("Retrieving data")
        elif user_lang(user_id) == 'rus':
            translator = GoogleTranslator(target='ru', source='uz')
            caption = translator.translate(caption)
            await call.answer("Извлечение данных")

        media = [types.InputMediaPhoto(media=InputFile(f'handlers/images/bomdod_time.jpg',
                                                       'bomdod_time.jpg'),
                                       caption=caption)]
        await call.message.edit_media(media=media[0],
                                      reply_markup=back_btns(user_id))
        await USER.day_parts.set()
    elif callback == 'peshin':
        req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
        peshin = req['times']['peshin']
        day = req['weekday']
        date = req['date']

        bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
        creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
        caption = (f"<code>{region} - uchun Peshin namozi vaqti!\n\nHafta kuni: {day}\nSana: {date}\n\n"
                   f"👉 Peshin: {peshin}</code>\n\n{bot_link}\n{creator}")

        if user_lang(user_id) == 'uzb':
            caption = caption
            await call.answer("Ma'lumotlar olinmoqda")
        elif user_lang(user_id) == 'eng':
            translator = GoogleTranslator(target='en', source='uz')
            caption = translator.translate(caption)
            await call.answer("Retrieving data")
        elif user_lang(user_id) == 'rus':
            translator = GoogleTranslator(target='ru', source='uz')
            caption = translator.translate(caption)
            await call.answer("Извлечение данных")

        media = [types.InputMediaPhoto(media=InputFile(f'handlers/images/peshin_time.jpg',
                                                       'peshin_time.jpg'),
                                       caption=caption)]
        await call.message.edit_media(media=media[0],
                                      reply_markup=back_btns(user_id))
        await USER.day_parts.set()
    elif callback == 'asr':
        req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
        asr = req['times']['asr']
        day = req['weekday']
        date = req['date']

        bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
        creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
        caption = (f"<code>{region} - uchun Asr namozi vaqti!\n\nHafta kuni: {day}\nSana: {date}\n\n"
                   f"👉 Peshin: {asr}</code>\n\n{bot_link}\n{creator}")

        if user_lang(user_id) == 'uzb':
            caption = caption
            await call.answer("Ma'lumotlar olinmoqda")
        elif user_lang(user_id) == 'eng':
            translator = GoogleTranslator(target='en', source='uz')
            caption = translator.translate(caption)
            await call.answer("Retrieving data")
        elif user_lang(user_id) == 'rus':
            translator = GoogleTranslator(target='ru', source='uz')
            caption = translator.translate(caption)
            await call.answer("Извлечение данных")

        media = [types.InputMediaPhoto(media=InputFile(f'handlers/images/asr_time.jpg',
                                                       'asr_time.jpg'),
                                       caption=caption)]
        await call.message.edit_media(media=media[0],
                                      reply_markup=back_btns(user_id))
        await USER.day_parts.set()
    elif callback == 'shom':
        req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
        shom = req['times']['shom_iftor']
        day = req['weekday']
        date = req['date']

        bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
        creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
        caption = (f"<code>{region} - uchun Shom namozi vaqti!\n\nHafta kuni: {day}\nSana: {date}\n\n"
                   f"👉 Shom (Iftorlik): {shom}</code>\n\n{bot_link}\n{creator}")

        if user_lang(user_id) == 'uzb':
            caption = caption
            await call.answer("Ma'lumotlar olinmoqda")
        elif user_lang(user_id) == 'eng':
            translator = GoogleTranslator(target='en', source='uz')
            caption = translator.translate(caption)
            await call.answer("Retrieving data")
        elif user_lang(user_id) == 'rus':
            translator = GoogleTranslator(target='ru', source='uz')
            caption = translator.translate(caption)
            await call.answer("Извлечение данных")

        media = [types.InputMediaPhoto(media=InputFile(f'handlers/images/shom_time.jpg',
                                                       'shom_time.jpg'),
                                       caption=caption)]
        await call.message.edit_media(media=media[0],
                                      reply_markup=back_btns(user_id))
        await USER.day_parts.set()
    elif callback == 'xufton':
        req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
        xufton = req['times']['hufton']
        day = req['weekday']
        date = req['date']

        bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
        creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
        caption = (f"<code>{region} - uchun Xufton namozi vaqti!\n\nHafta kuni: {day}\nSana: {date}\n\n"
                   f"👉 Xufton: {xufton}</code>\n\n{bot_link}\n{creator}")

        if user_lang(user_id) == 'uzb':
            caption = caption
            await call.answer("Ma'lumotlar olinmoqda")
        elif user_lang(user_id) == 'eng':
            translator = GoogleTranslator(target='en', source='uz')
            caption = translator.translate(caption)
            await call.answer("Retrieving data")
        elif user_lang(user_id) == 'rus':
            translator = GoogleTranslator(target='ru', source='uz')
            caption = translator.translate(caption)
            await call.answer("Извлечение данных")

        media = [types.InputMediaPhoto(media=InputFile(f'handlers/images/xufton_time.jpg',
                                                       'xufton_time.jpg'),
                                       caption=caption)]
        await call.message.edit_media(media=media[0],
                                      reply_markup=back_btns(user_id))
        await USER.day_parts.set()
    elif callback == 'today':
        req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
        day = req['weekday']
        date = req['date']
        fajr = req['times']['tong_saharlik']
        sunrise = req['times']['quyosh']
        peshin = req['times']['peshin']
        asr = req['times']['asr']
        shom = req['times']['shom_iftor']
        hufton = req['times']['hufton']

        caption = (f"<code>{region} - uchun bugungi namoz vaqtlari!\n\n"
                   f"Hafta kuni: {day}\nSana: {date}\n\n"
                   f"👉 Bomdod (Saharlik): {fajr}\n"
                   f"👉 Quyosh chiqishi: {sunrise}\n"
                   f"👉 Peshin: {peshin}\n"
                   f"👉 Asr: {asr}\n"
                   f"👉 Shom: {shom}\n"
                   f"👉 Xufton: {hufton}</code>\n\n")
        caption += (f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>\n"
                    f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>")

        media = [types.InputMediaPhoto(media=InputFile(f'handlers/images/today_times.jpg',
                                                       'today_times.jpg'),
                                       caption=caption)]
        await call.message.edit_media(media=media[0],
                                      reply_markup=back_btns(user_id))
        await USER.day_parts.set()
    elif callback == 'this_week':
        await call.message.delete()
        req = requests.get(url=f"https://islomapi.uz/api/present/week?region={region}").json()
        full_caption = ''
        for item in req:
            date_time = item['date']
            date_part = date_time.split(",")[0]

            region = item['region']
            weekday = item['weekday']
            times = item['times']

            caption = f"<code><b>👇👇 Hudud: {region} 👇👇</b>\n" \
                      f"Namoz vaqtlari: <b>{date_part}</b>\n" \
                      f"Quyosh chiqishi: <b>{times['quyosh']}</b>\n\n" \
                      f"Hafta kuni: <b>{weekday}</b>\n"
            for key, value in times.items():
                caption += f"👉 {key.capitalize()}: <b>{value}</b>\n"

            caption += "</code>\n\n"
            full_caption += caption
        full_caption += f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>\n"
        full_caption += f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"

        await bot.send_message(chat_id=user_id, text=full_caption, reply_markup=back_btns(user_id))
        await USER.week_times.set()

    elif callback == 'back':
        media = [types.InputMediaPhoto(media=InputFile("handlers/images/prayer_times.png",
                                                       "prayer_times.png"), caption='Viloyatlar ro\'yxati 👇')]
        await call.message.edit_media(media=media[0], reply_markup=regions_list(user_id))
        await USER.main_menu.set()
    else:
        await call.answer("Error code: 404")


@dp.callback_query_handler(state=USER.day_parts)
async def going_back(call: types.CallbackQuery, state: FSMContext):
    callback = call.data
    user_id = call.from_user.id

    if callback == 'back_to_day':
        datas = await state.get_data()
        region = datas.get('region')
        call_region = datas.get('region_callback')
        caption = f"{region} uchun namoz vaqtlari 👇"

        if user_lang(user_id) == 'uzb':
            caption = caption
            org_region = region
            await state.update_data({'region': org_region})
        elif user_lang(user_id) == 'eng':
            org_region = region
            await state.update_data({'region': org_region})
            translator = GoogleTranslator(target='en', source='uz')
            caption = translator.translate(caption)
        elif user_lang(user_id) == 'rus':
            org_region = region
            await state.update_data({'region': org_region})
            translator = GoogleTranslator(target='ru', source='uz')
            caption = translator.translate(caption)

        media = [types.InputMediaPhoto(media=InputFile(f'handlers/images/{call_region}.jpg',
                                                       f'{call_region}.jpg'),
                                       caption=caption)]
        await call.message.edit_media(media=media[0], reply_markup=day_part(user_id))
        await USER.region.set()
    elif callback == 'go_home':
        media = [types.InputMediaPhoto(media=InputFile("handlers/images/prayer_times.png",
                                                       "prayer_times.png"), caption='Viloyatlar ro\'yxati 👇')]
        await call.message.edit_media(media=media[0], reply_markup=regions_list(user_id))
        await USER.main_menu.set()
    else:
        await call.answer("Error code: 404")


@dp.callback_query_handler(state=USER.week_times)
async def back_from_weekly(call: types.CallbackQuery, state: FSMContext):
    callback = call.data
    user_id = call.from_user.id

    if callback == 'back_to_day':
        datas = await state.get_data()
        region = datas.get('region')
        call_region = datas.get('region_callback')
        caption = f"{region} uchun namoz vaqtlari 👇"

        if user_lang(user_id) == 'uzb':
            caption = caption
            org_region = region
            await state.update_data({'region': org_region})
        elif user_lang(user_id) == 'eng':
            org_region = region
            await state.update_data({'region': org_region})
            translator = GoogleTranslator(target='en', source='uz')
            caption = translator.translate(caption)
        elif user_lang(user_id) == 'rus':
            org_region = region
            await state.update_data({'region': org_region})
            translator = GoogleTranslator(target='ru', source='uz')
            caption = translator.translate(caption)

        with open(f"handlers/images/{call_region}.jpg", 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=user_id, caption=caption, reply_markup=day_part(user_id))
        await call.message.delete_reply_markup()
        await USER.region.set()
    elif callback == 'go_home':
        pass
    else:
        await call.answer("Error code: 404")
