import mysql.connector
from aiogram import types
from aiogram.dispatcher.filters import CommandStart, Text

from deep_translator import GoogleTranslator

from data.config import *
from keyboards.default.admin_kb import admin_kb
from keyboards.default.user_kb import user_kb
from keyboards.inline.admin_ikb import admin_ikb
from keyboards.inline.user_ikb import user_ikb
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


def is_admin(user_id):
    for admin in ADMINS:
        if int(user_id) == int(admin):
            return 1
        else:
            return 0


@dp.message_handler(CommandStart())
async def start_bot(message: types.Message):
    user = message.from_user.first_name
    user_id = message.from_user.id

    select_query = 'select user_id from users_list'
    cursor.execute(select_query)
    users = cursor.fetchall()
    db_connection.commit()
    print(users)
    is_member = []
    for user in users:
        if int(user_id) == int(user[0]):
            is_member.append(user_id)

    if len(is_member) <= 0:
        if is_admin(user_id=user_id) == 1:
            await message.answer(f"Assalomu alaykum, {user}\n\nSelect the desired language\nKerakli tilni tanlang"
                                 f"\nВыберите желаемый язык\n\nEnglish👇 | O'zbekcha👇 | Русский👇",
                                 reply_markup=admin_ikb())
            await ADMIN.start.set()
        else:
            await message.answer(f"Assalomu alaykum {user}\n\nSelect the desired language\nKerakli tilni tanlang"
                                 f"\nВыберите желаемый язык\n\nEnglish👇 | O'zbekcha👇 | Русский👇",
                                 reply_markup=user_ikb())
            await USER.start.set()
    else:
        message_text = "Botdan foydalanishingiz mumkin 🤗\n\nYordam olish uchun /help komandasini yuboring!"
        if is_admin(user_id) == 1:
            if user_lang(user_id) == 'uzb':
                message_text = message_text
            elif user_lang(user_id) == 'eng':
                translator = GoogleTranslator(target='en', source='uz')
                message_text = translator.translate(message_text)
            elif user_lang(user_id) == 'rus':
                translator = GoogleTranslator(target='ru', source='uz')
                message_text = translator.translate(message_text)
            await message.answer(message_text, reply_markup=admin_kb(user_id))
            await ADMIN.main_menu.set()
        else:
            if user_lang(user_id) == 'uzb':
                message_text = message_text
            elif user_lang(user_id) == 'eng':
                translator = GoogleTranslator(target='en', source='uz')
                message_text = translator.translate(message_text)
            elif user_lang(user_id) == 'rus':
                translator = GoogleTranslator(target='ru', source='uz')
                message_text = translator.translate(message_text)
            await message.answer(message_text, reply_markup=user_kb(user_id))
            await USER.main_menu.set()


@dp.callback_query_handler(state=[ADMIN.start, USER.start])
async def select_lang(call: types.CallbackQuery):
    callback = call.data
    user_name = call.from_user.first_name
    user_id = call.from_user.id
    username = f"@{call.from_user.username}"
    is_user_admin = is_admin(user_id)
    lang = call.data

    query_insert = 'insert into users_list(user_name, user_id, username, is_admin, lang) values(%s, %s, %s, %s, %s)'
    value_insert = (user_name, user_id, username, is_user_admin, lang)
    cursor.execute(query_insert, value_insert)
    db_connection.commit()

    message_text = "Botdan foydalanishingiz mumkin 🤗\n\nYordam olish uchun /help komandasini yuboring!"

    if callback == 'eng':
        await call.answer("You have selected English")
        translator = GoogleTranslator(target='en', source='uz')
        message_text = translator.translate(message_text)
    elif callback == 'uzb':
        await call.answer("Siz o'zbek tilini tanladingiz")
        message_text = message_text
    elif callback == 'rus':
        await call.answer("Вы выбрали русский")
        translator = GoogleTranslator(target='ru', source='uz')
        message_text = translator.translate(message_text)

    if is_admin(user_id):
        await bot.send_message(chat_id=user_id, text=message_text, reply_markup=admin_kb(user_id=user_id))
    else:
        await bot.send_message(chat_id=user_id, text=message_text, reply_markup=user_kb(user_id=user_id))
    await call.message.delete()
