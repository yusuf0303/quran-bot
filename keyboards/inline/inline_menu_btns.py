from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def surah_ikb():
    surah = InlineKeyboardMarkup(row_width=3)
    text = InlineKeyboardButton(text="Sura matni 📃", callback_data='text')
    trans = InlineKeyboardButton(text="Tarjimasi 📃", callback_data='translation')
    audio = InlineKeyboardButton(text="Audiosi 🎧", callback_data='audio_surah')
    ayah = InlineKeyboardButton(text="Oyatlar 📄", callback_data='ayah')
    back = InlineKeyboardButton(text="⬅️ Suralar", callback_data='go_home')

    surah.add(text, trans).add(audio, ayah).add(back)
    return surah
