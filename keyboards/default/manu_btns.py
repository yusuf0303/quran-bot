from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_btns():
    users_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2, keyboard=[[
        KeyboardButton(text="Suralar 🔍"),
        KeyboardButton(text="Oyatlar 🔍")
    ]], one_time_keyboard=True)
    prayer_times = KeyboardButton(text="Namoz vaqtlari 🕌")
    settings = KeyboardButton(text="Sozlamalar 🛠")
    favourites = KeyboardButton(text="Sevimlilar 💖")
    users_kb.add(prayer_times).add(favourites, settings)
    return users_kb
