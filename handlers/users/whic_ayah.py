import requests
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher.filters.builtin import Text

from keyboards.default.manu_btns import main_btns
from loader import dp, bot


@dp.message_handler(Text(equals='Oyatlar 🔍'), state='*')
async def which_ayah(message: types.Message, state: FSMContext):
    test_btns = ReplyKeyboardMarkup(
        resize_keyboard=True, row_width=1,
        keyboard=[
            [KeyboardButton(text="O'yinni boshlash")],
            [KeyboardButton(text="⬅️ Menyuga qaytish")]
        ])
    await message.answer(text="Bu qaysi oyat o'yiniga xush kelibsiz 🤗", reply_markup=test_btns)
    await state.finish()


@dp.message_handler(Text(equals="⬅️ Menyuga qaytish"))
async def go_home(message: types.Message):
    await message.answer(text="Bosh menyu, bo'limlardan birni tanlang 👇", reply_markup=main_btns())


@dp.message_handler(Text(equals="O'yinni boshlash"))
async def starting_game(message: types.Message):
    juz_btns = ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
    btns = []
    for juz in range(1, 31):
        # get_juz = requests.get(url=f"https://api.alquran.cloud/v1/juz/{juz}/en.asad").json()
        # juz_number = get_juz['data']['ayahs'][juz]['juz']
        btns.append(KeyboardButton(text=f"{juz}"))
    all_juz = KeyboardButton(text="Barchasini tanlash ☑️")
    back_home = KeyboardButton(text="⬅️ Menyuga qaytish")
    juz_btns.add(all_juz).add(*btns).add(back_home)

    await message.answer(text="Nechanchi juzdan boshlaymiz?", reply_markup=juz_btns)


# @dp.message_handler()
# async def game_started(message: types.Message):
#     if message.text.isdigit() and 0 < int(message.text) < 31:
#         await message.answer("Ushbu bo'lim ishlovda, tez orada ishga tushdi")
#     else:
#         await message.answer("Ushbu bo'lim ishlovda, tez orada ishga tushdi")
