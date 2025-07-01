from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def surah_ikb():
    keyboard = [
        [
            InlineKeyboardButton("📜 Oyatlar", callback_data=f"list_ayahs"),  # <- Sura raqamini qo'shamiz
            InlineKeyboardButton("🎧 Audio", callback_data=f"audio_surah")
        ],
        [
            InlineKeyboardButton("📖 Suralar", callback_data='show_surahs_list')]
    ]
    return InlineKeyboardMarkup(keyboard)

def surah_ikb2():
    keyboard = [

        [
            InlineKeyboardButton("📜 Oyatlar", callback_data=f"list_ayahs"),  # <- Sura raqamini qo'shamiz
            InlineKeyboardButton("🎧 Audio", callback_data=f"audio_surah")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)