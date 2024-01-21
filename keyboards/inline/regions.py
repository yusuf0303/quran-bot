import mysql.connector
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import *

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


def regions_list(user_id):
    if user_lang(user_id) == 'uzb':
        regions = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Toshkent", callback_data='tashkent')],
                [InlineKeyboardButton(text="Samarqand", callback_data='samarkand'),
                 InlineKeyboardButton(text="Andijon", callback_data='andijon')],
                [InlineKeyboardButton(text="Buxoro", callback_data='buxoro'),
                 InlineKeyboardButton(text="Farg'ona", callback_data='fargona')],
                [InlineKeyboardButton(text="Guliston", callback_data='guliston'),
                 InlineKeyboardButton(text="Jizzax", callback_data='jizzax')],
                [InlineKeyboardButton(text="Qarshi", callback_data='qarshi'),
                 InlineKeyboardButton(text="Namangan", callback_data='namangan')],
                [InlineKeyboardButton(text="Navoiy", callback_data='navoiy'),
                 InlineKeyboardButton(text="Xiva", callback_data='xiva')],
                [InlineKeyboardButton(text="Nukus ( Qoraqalpog'iston Res )", callback_data='nukus')]
            ],
            row_width=2
        )
        return regions
    elif user_lang(user_id) == 'eng':
        regions = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Tashkent", callback_data='tashkent')],
                [InlineKeyboardButton(text="Samarkand", callback_data='samarkand'),
                 InlineKeyboardButton(text="Andijan", callback_data='andijon')],
                [InlineKeyboardButton(text="Bukhara", callback_data='buxoro'),
                 InlineKeyboardButton(text="Ferghana", callback_data='fargona')],
                [InlineKeyboardButton(text="Gulistan", callback_data='guliston'),
                 InlineKeyboardButton(text="Jizzakh", callback_data='jizzax')],
                [InlineKeyboardButton(text="Karshi", callback_data='qarshi'),
                 InlineKeyboardButton(text="Namangan", callback_data='namangan')],
                [InlineKeyboardButton(text="Navoi", callback_data='navoiy'),
                 InlineKeyboardButton(text="Khiva", callback_data='xiva')],
                [InlineKeyboardButton(text="Nukus (Karakalpagistan Res)", callback_data='nukus')]
            ],
            row_width=2
        )
        return regions
    elif user_lang(user_id) == 'rus':
        regions = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Ташкенте", callback_data='tashkent')],
                [InlineKeyboardButton(text="Самарканде", callback_data='samarkand'),
                 InlineKeyboardButton(text="Андижане", callback_data='andijon')],
                [InlineKeyboardButton(text="Бухаре", callback_data='buxoro'),
                 InlineKeyboardButton(text="Фергану", callback_data='fargona')],
                [InlineKeyboardButton(text="Гулистан", callback_data='guliston'),
                 InlineKeyboardButton(text="Джизаке", callback_data='jizzax')],
                [InlineKeyboardButton(text="Карши", callback_data='qarshi'),
                 InlineKeyboardButton(text="Намангане", callback_data='namangan')],
                [InlineKeyboardButton(text="Навои", callback_data='navoiy'),
                 InlineKeyboardButton(text="Хиву", callback_data='xiva')],
                [InlineKeyboardButton(text="Нукусе (Каракалпакский Рес)", callback_data='nukus')]
            ],
            row_width=2
        )
        return regions


def day_part(user_id):
    if user_lang(user_id) == 'uzb':
        back_region = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Bomdod 🌅", callback_data='bomdod'),
                 InlineKeyboardButton(text="Peshin 🕑", callback_data='peshin'),
                 InlineKeyboardButton(text="Asr 🌇", callback_data='asr')],
                [InlineKeyboardButton(text="Shom 🌆", callback_data='shom'),
                 InlineKeyboardButton(text="Xufton 🌃", callback_data='xufton')],
                [InlineKeyboardButton(text="Bugun ( To'liq ) 📅", callback_data='today'),
                 InlineKeyboardButton(text="Shu hafta ( To'liq ) 🗓️", callback_data='this_week')],
                [InlineKeyboardButton(text="⬅️ Orqaga", callback_data='back')]
            ],
            row_width=2
        )
        return back_region
    elif user_lang(user_id) == 'eng':
        back_region = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Fajr 🌅", callback_data='bomdod'),
                 InlineKeyboardButton(text="Dhuhr 🕑", callback_data='peshin'),
                 InlineKeyboardButton(text="Asr 🌇", callback_data='asr')],
                [InlineKeyboardButton(text="Maghrib 🌆", callback_data='shom'),
                 InlineKeyboardButton(text="Isha 🌃", callback_data='xufton')],
                [InlineKeyboardButton(text="Today ( Full ) 📅", callback_data='today'),
                 InlineKeyboardButton(text="This week ( Full ) 🗓️", callback_data='this_week')],
                [InlineKeyboardButton(text="⬅️ Back", callback_data='back')]
            ],
            row_width=2
        )
        return back_region
    elif user_lang(user_id) == 'rus':
        back_region = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Фаджр 🌅", callback_data='bomdod'),
                 InlineKeyboardButton(text="Зухр 🕑", callback_data='peshin'),
                 InlineKeyboardButton(text="Аср 🌇", callback_data='asr')],
                [InlineKeyboardButton(text="Магриб 🌆", callback_data='shom'),
                 InlineKeyboardButton(text="Иша 🌃", callback_data='xufton')],
                [InlineKeyboardButton(text="Сегодня (Полная версия) 📅", callback_data='today'),
                 InlineKeyboardButton(text="На этой неделе (полная версия) 🗓️", callback_data='this_week')],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data='back')]
            ],
            row_width=2
        )
        return back_region


def back_btns(user_id):
    if user_lang(user_id) == 'uzb':
        backs = InlineKeyboardMarkup(row_width=2, inline_keyboard=[[
            InlineKeyboardButton(text="⬅️ Orqaga", callback_data='back_to_day'),
            InlineKeyboardButton(text="🔝 Bosh menyuga", callback_data='go_home')
        ]])
        return backs
    elif user_lang(user_id) == 'eng':
        backs = InlineKeyboardMarkup(row_width=2, inline_keyboard=[[
            InlineKeyboardButton(text="⬅️ Back", callback_data='back_to_day'),
            InlineKeyboardButton(text="🔝 To main menu", callback_data='go_home')
        ]])
        return backs
    elif user_lang(user_id) == 'rus':
        backs = InlineKeyboardMarkup(row_width=2, inline_keyboard=[[
            InlineKeyboardButton(text="⬅️ Назад", callback_data='back_to_day'),
            InlineKeyboardButton(text="🔝 В главное меню", callback_data='go_home')
        ]])
        return backs
