from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def regions():
    region_btns = InlineKeyboardMarkup(row_width=3, inline_keyboard=[
        [InlineKeyboardButton(text="Toshkent", callback_data='Toshkent'),
         InlineKeyboardButton(text="Samarqand", callback_data='Samarqand')],
        [InlineKeyboardButton(text="Andijon", callback_data='Andijon'),
         InlineKeyboardButton(text="Buxoro", callback_data='Buxoro')],
        [InlineKeyboardButton(text="Farg'ona", callback_data="Farg'ona"),
         InlineKeyboardButton(text="Guliston", callback_data="Guliston")],
        [InlineKeyboardButton(text="Jizzax", callback_data="Jizzax"),
         InlineKeyboardButton(text="Qarshi", callback_data="Qarshi")],
        [InlineKeyboardButton(text="Namangan", callback_data="Namangan"),
         InlineKeyboardButton(text="Navoiy", callback_data="Navoiy")],
        [InlineKeyboardButton(text="Xiva", callback_data="Xiva"),
         InlineKeyboardButton(text="Nukus", callback_data="Nukus")]
    ])
    return region_btns


def prayer_times_btn():
    back_region = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Bomdod 🌅", callback_data='tong_saharlik'),
             InlineKeyboardButton(text="Peshin 🕑", callback_data='peshin')],
            [InlineKeyboardButton(text="Asr 🌇", callback_data='asr'),
             InlineKeyboardButton(text="Shom 🌆", callback_data='shom_iftor'),
             InlineKeyboardButton(text="Xufton 🌃", callback_data='xufton')],
            [InlineKeyboardButton(text="Bugun ( To'liq ) 📅", callback_data='today'),
             InlineKeyboardButton(text="Shu hafta ( To'liq ) 🗓️", callback_data='week')],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data='back_to_regions'),
             InlineKeyboardButton(text="Quyosh chiqishi 🌄", callback_data='quyosh')]
        ]
    )
    return back_region
