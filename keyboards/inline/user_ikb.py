from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def user_ikb():
    users_ikb = InlineKeyboardMarkup(row_width=3, inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇸", callback_data='eng'),
        InlineKeyboardButton(text="🇺🇿", callback_data='uzb'),
        InlineKeyboardButton(text="🇷🇺", callback_data='rus')
    ]])
    return users_ikb

