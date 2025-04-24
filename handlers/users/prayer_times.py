from aiogram import types
import requests

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import Command
from aiogram.dispatcher.filters import Text
from aiogram.types import InputMedia

from keyboards.inline.inline_prayer_times import regions, prayer_times_btn
from loader import dp, bot
from states.prayer_times import PrayerTime


@dp.message_handler(Text(equals="Namoz vaqtlari 🕌"), state='*')
async def prayer_times(message: types.Message, state: FSMContext):
    with open("handlers/images/prayer_times.png", 'rb') as photo:
        await bot.send_photo(photo=photo, chat_id=message.from_user.id, caption="Viloyatlardan birini tanlang",
                             reply_markup=regions())
    # await state.finish()
    await PrayerTime.region.set()


@dp.callback_query_handler(state=PrayerTime.region)
async def get_regions(call: types.CallbackQuery, state: FSMContext):
    callback = call.data
    await call.answer(callback)
    current_state = await state.get_state()
    if current_state == "StartCMD:surah_menu":
        await call.answer("Xabar eskirgan")
    else:
        if "'" in callback:
            callback = callback.replace("'", '').lower()
        else:
            callback = callback.lower()

        # else:
        await call.message.delete()
        with open(f"handlers/images/{callback}.jpg", 'rb') as photo:
            await bot.send_photo(chat_id=call.from_user.id, photo=photo,
                                 caption=f"<b><i>{callback.capitalize()} viloyati (shahri)</i></b> uchun namoz "
                                         f"vaqtlaridan birini tanlang",
                                 reply_markup=prayer_times_btn(),
                                 parse_mode="HTML")
        await state.update_data(
            {'region': callback.capitalize()}
        )
        await PrayerTime.prayer_time_lim.set()


def pray_times(request_times, user_id):
    prayers_time = {f"{user_id}":
                    {'bomdod': request_times['times']['tong_saharlik'],
                     'quyosh': request_times['times']['quyosh'],
                     'peshin': request_times['times']['peshin'],
                     'asr': request_times['times']['asr'],
                     'shom': request_times['times']['shom_iftor'],
                     'hufton': request_times['times']['hufton'],
                     'date': request_times['date'],
                     'weekday': request_times['weekday'],
                     'hijri_oy': request_times['hijri_date']['month'],
                     'hijri_kun': request_times['hijri_date']['day'],
                     'hudud': request_times['region']}}
    return prayers_time


@dp.callback_query_handler(state=PrayerTime.prayer_time_lim)
async def get_times(call: types.CallbackQuery, state: FSMContext):
    callback = call.data
    user_id = call.from_user.id
    # await call.answer(callback)
    if callback == 'back_to_regions':
        await call.answer("Viloyatlar")
        await call.message.delete()
        with open("handlers/images/prayer_times.png", 'rb') as photo:
            await bot.send_photo(photo=photo, chat_id=call.from_user.id, caption="Viloyatlardan birini tanlang",
                                 reply_markup=regions())
        await PrayerTime.region.set()
    # elif callback == 'bomdod':
    #     pass
    else:
        datas = await state.get_data()
        region = datas.get('region')
        request_times = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
        print(request_times.keys())
        print(pray_times(request_times=request_times, user_id=user_id))
        print(str(callback.split(' ')[0]))
        text_msg = pray_times(request_times=request_times, user_id=user_id)[str(user_id)][str(call.message.text).split(' ')[0].lower()]
        await call.message.answer(text=text_msg)
        await call.answer(callback)
        for time in pray_times(request_times, user_id):
            print(time)


# @dp.callback_query_handler(state=PrayerTime.prayer_time_lim)
# async def fajr_time(callback: types.CallbackQuery, state: FSMContext):
#     call = callback.data
#
#     if call == "Bomdod 🌅":
#         data = await state.get_data()
#         region = data.get('region')
#         req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
#         fajr = req['times']['tong_saharlik']
#         sunrise = req['times']['quyosh']
#         day = req['weekday']
#         date = req['date']
#
#         bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
#         creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
#         await callback.message.answer(f"<code>{region} - uchun Bomdod namozi vaqti!\n\n"
#                                       f"Hafta kuni: {day}\nSana: {date}\n\n"
#                                       f"👉 Bomdod (Saharlik): {fajr}\n"
#                                       f"👉 Quyosh chiqishi: {sunrise}</code>\n\n"
#                                       f"{bot_link}\n{creator}",
#                                       parse_mode="HTML")
#     else:
#         await callback.answer("Working on it")

#
# from keyboards.default.regions import regions, back_region
#
#
# @dp.message_handler(Command('prayer_times'), state="*")
# @dp.message_handler(Text(equals="Namoz vaqtlari 🕌"), state="*")
# async def get_region(message: types.Message):
#     await message.answer("Hududingizni tanlang!",
#                          reply_markup=regions)
#
#
# @dp.message_handler(Text(equals="Menyuga qaytish 🔝"), state="*")
# async def go_home(message: types.Message):
#     await message.answer("Asosiy menyuga qaytdingiz!",
#                          reply_markup=main_btns())
#
#
# @dp.message_handler(Text(equals="Nukus ( Qoraqalpog'iston Res )"), state="*")
# async def get_time(message: types.Message, state: FSMContext):
#     nukus = message.text.rstrip(" ( Qoraqalpog'iston Res )") + 's'
#     await message.answer(f"<b><i>{nukus}  ( Qoraqalpog'iston Res )</i></b> uchun namoz vaqtlaridan birini tanlang",
#                          reply_markup=back_region,
#                          parse_mode="HTML")
#     await state.update_data(
#         {'region': nukus}
#     )
#     await PrayerTime.prayer_time_lim.set()
#
#
# @dp.message_handler(state="*")
# async def get_reg_time(message: types.Message, state: FSMContext):
#     reg_names = []
#     for row in regions.keyboard:
#         for btn in row:
#             reg_names.append(btn.text)
#     if message.text in reg_names:
#         await message.answer(f"<b><i>{message.text} viloyati (shahri)</i></b> uchun namoz vaqtlaridan birini tanlang",
#                              reply_markup=back_region,
#                              parse_mode="HTML")
#         await state.update_data(
#             {'region': message.text}
#         )
#         await PrayerTime.prayer_time_lim.set()
#     else:
#         await bot.send_message(chat_id=message.chat.id,
#                                text="Hududlardan birini tanlang 👇👇👇",
#                                reply_markup=regions)
#
#
# @dp.message_handler(Text(equals="⬅️ Orqaga"), state="*")
# async def go_back(message: types.Message, state: FSMContext):
#     await message.answer("Hududingizni tanlang!",
#                          reply_markup=regions)
#     await state.finish()
#     await PrayerTime.region.set()
#
#
# @dp.message_handler(Text(equals="Menyuga qaytish 🔝"), state="*")
# async def go_home(message: types.Message, state: FSMContext):
#     await message.answer("Asosiy menyuga qaytdingiz!",
#                          reply_markup=main_btns())
#     await state.finish()
#     await StartCMD.joined_channels.set()
#
#
# @dp.message_handler(Text(equals="Bomdod 🌅"), state="*")
# async def bomdod_cmd(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     region = data.get('region')
#     req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
#     fajr = req['times']['tong_saharlik']
#     sunrise = req['times']['quyosh']
#     day = req['weekday']
#     date = req['date']
#
#     bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
#     creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
#     await message.answer(f"<code>{region} - uchun Bomdod namozi vaqti!\n\n"
#                          f"Hafta kuni: {day}\nSana: {date}\n\n"
#                          f"👉 Bomdod (Saharlik): {fajr}\n"
#                          f"👉 Quyosh chiqishi: {sunrise}</code>\n\n"
#                          f"{bot_link}\n{creator}",
#                          parse_mode="HTML",
#                          reply_markup=back_region)
#
#
# @dp.message_handler(Text(equals="Peshin 🕑"), state="*")
# async def peshin_cmd(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     region = data.get('region')
#     req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
#     peshin = req['times']['peshin']
#     day = req['weekday']
#     date = req['date']
#
#     bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
#     creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
#     await message.answer(f"<code>{region} - uchun Peshin namozi vaqti!\n\n"
#                          f"Hafta kuni: {day}\nSana: {date}\n\n"
#                          f"👉 Peshin: {peshin}</code>\n\n"
#                          f"{bot_link}\n{creator}",
#                          parse_mode="HTML",
#                          reply_markup=back_region)
#
#
# @dp.message_handler(Text(equals="Asr 🌇"), state="*")
# async def asr_cmd(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     region = data.get('region')
#     req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
#     asr = req['times']['asr']
#     day = req['weekday']
#     date = req['date']
#
#     bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
#     creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
#     await message.answer(f"<code>{region} - uchun Asr namozi vaqti!\n\n"
#                          f"Hafta kuni: {day}\nSana: {date}\n\n"
#                          f"👉 Asr: {asr}</code>\n\n"
#                          f"{bot_link}\n{creator}",
#                          parse_mode="HTML",
#                          reply_markup=back_region)
#
#
# @dp.message_handler(Text(equals="Shom 🌆"), state="*")
# async def shom_cmd(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     region = data.get('region')
#     req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
#     shom = req['times']['shom_iftor']
#     day = req['weekday']
#     date = req['date']
#
#     bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
#     creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
#     await message.answer(f"<code>{region} - uchun Shom namozi vaqti!\n\n"
#                          f"Hafta kuni: {day}\nSana: {date}\n\n"
#                          f"👉 Shom (Iftorlik): {shom}</code>\n\n"
#                          f"{bot_link}\n{creator}",
#                          parse_mode="HTML",
#                          reply_markup=back_region)
#
#
# @dp.message_handler(Text(equals="Xufton 🌃"), state="*")
# async def xufton_cmd(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     region = data.get('region')
#     req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
#     hufton = req['times']['hufton']
#     day = req['weekday']
#     date = req['date']
#
#     bot_link = f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>"
#     creator = f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
#     await message.answer(f"<code>{region} - uchun Xufton namozi vaqti!\n\n"
#                          f"Hafta kuni: {day}\nSana: {date}\n\n"
#                          f"👉 Xufton: {hufton}</code>\n\n"
#                          f"{bot_link}\n{creator}",
#                          parse_mode="HTML",
#                          reply_markup=back_region)
#
#
# @dp.message_handler(Text(equals="Bugun ( To'liq ) 📅"), state="*")
# async def today_cmd(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     region = data.get('region')
#     req = requests.get(url=f"https://islomapi.uz/api/present/day?region={region}").json()
#     day = req['weekday']
#     date = req['date']
#     fajr = req['times']['tong_saharlik']
#     sunrise = req['times']['quyosh']
#     peshin = req['times']['peshin']
#     asr = req['times']['asr']
#     shom = req['times']['shom_iftor']
#     hufton = req['times']['hufton']
#
#     msg_text = (f"<code>{region} - uchun bugungi namoz vaqtlari!\n\n"
#                 f"Hafta kuni: {day}\nSana: {date}\n\n"
#                 f"👉 Bomdod (Saharlik): {fajr}\n"
#                 f"👉 Quyosh chiqishi: {sunrise}\n"
#                 f"👉 Peshin: {peshin}\n"
#                 f"👉 Asr: {asr}\n"
#                 f"👉 Shom: {shom}\n"
#                 f"👉 Xufton: {hufton}</code>\n\n")
#
#     msg_text += f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>\n"
#     msg_text += f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
#     await message.answer(text=msg_text,
#                          parse_mode="HTML",
#                          reply_markup=back_region)
#
#
# @dp.message_handler(Text(equals="Shu hafta ( To'liq ) 🗓️"), state="*")
# async def this_week_cmd(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     region = data.get('region')
#     req = requests.get(url=f"https://islomapi.uz/api/present/week?region={region}").json()
#     full_caption = ''
#     for item in req:
#         date_time = item['date']
#         date_part = date_time.split(",")[0]
#
#         region = item['region']
#         weekday = item['weekday']
#         times = item['times']
#
#         caption = f"<code><b>👇👇 Hudud: {region} 👇👇</b>\n" \
#                   f"Namoz vaqtlari: <b>{date_part}</b>\n" \
#                   f"Quyosh chiqishi: <b>{times['quyosh']}</b>\n\n" \
#                   f"Hafta kuni: <b>{weekday}</b>\n"
#         for key, value in times.items():
#             caption += f"👉 {key.capitalize()}: <b>{value}</b>\n"
#
#         caption += "</code>\n\n"
#         full_caption += caption
#     full_caption += f"<a href='https://t.me/test_132_robot'>Quran By Ayah Bot 🤖</a>\n"
#     full_caption += f"<a href='https://t.me/R_Yusuf_Bot'>Created by SmartCoder 🧑‍💻</a>"
#
#     await bot.send_message(chat_id=message.chat.id,
#                            text=full_caption,
#                            parse_mode="HTML",
#                            reply_markup=back_region)
#
#
# @dp.message_handler(state="*")
# async def other_cmd(message: types.Message, state: FSMContext):
#     await message.answer(text="Iltimos, quyidagi bo'limlardan birini tanlang 👇",
#                          reply_markup=back_region)
