from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_ikb():
    admins_ikb = InlineKeyboardMarkup(row_width=3, inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇸", callback_data='eng'),
        InlineKeyboardButton(text="🇺🇿", callback_data='uzb'),
        InlineKeyboardButton(text="🇷🇺", callback_data='rus')
    ]])
    return admins_ikb
