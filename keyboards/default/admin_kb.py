from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from data.config import *

import mysql.connector

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


def admin_kb(user_id):

    if user_lang(user_id) == 'uzb':
        users_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, keyboard=[[
            KeyboardButton(text="Suralar 🔍"),
            KeyboardButton(text="Oyatlar 🔍")
        ]])
        prayer_times = KeyboardButton(text="Namoz vaqtlari 🕌")
        settings = KeyboardButton(text="Sozlamalar 🛠")
        users_kb.add(prayer_times).add(settings)
        return users_kb
    elif user_lang(user_id) == 'eng':
        users_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, keyboard=[[
            KeyboardButton(text="Surah 🔍"),
            KeyboardButton(text="Ayahs 🔍")
        ]])
        prayer_times = KeyboardButton(text="Prayer times 🕌")
        settings = KeyboardButton(text="Settings 🛠")
        users_kb.add(prayer_times).add(settings)
        return users_kb
    elif user_lang(user_id) == 'rus':
        users_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, keyboard=[[
            KeyboardButton(text="Сура 🔍"),
            KeyboardButton(text="Аяты 🔍")
        ]])
        prayer_times = KeyboardButton(text="Время молитвы 🕌")
        settings = KeyboardButton(text="Настройки 🛠")
        users_kb.add(prayer_times).add(settings)
        return users_kb
