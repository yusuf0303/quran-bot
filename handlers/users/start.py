import requests
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart, Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from deep_translator import GoogleTranslator

from keyboards.default.manu_btns import main_btns
from keyboards.inline.inline_menu_btns import surah_ikb
from loader import dp, bot
from states.start import StartCMD

surah_list = {}
caption_list = []
ayah_list = []
part_1_id = {}
# temp = {}


@dp.message_handler(CommandStart(), state='*')
async def bot_start(message: types.Message, state: FSMContext):
    share_button = types.InlineKeyboardButton(
        "Do'stlarga ulashish ⤴️", switch_inline_query='👈 ushbu botga kiring va men bilan Quronni yod oling!'
    )
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(share_button)
    await message.answer(f"Assalomu alaykum, {message.from_user.full_name}!\nOnline Quron botiga xush kelibsiz 🤗\n\n"
                         f"Biz bilan Quron o'rganishingiz ancha oson bo'ladi, In Shaa Alloh 😊\n\nBotni yaqinlaringizga "
                         f"ham ulashing zero siz sabab bir kishi undan foyda olsa savobiga siz ham sherik bo'lasiz ☪️",
                         reply_markup=keyboard)
    await message.answer("Quyidagi bo'limlardan birini tanlang 👇", reply_markup=main_btns())
    await state.finish()


@dp.message_handler(Text(equals=["Suralar 🔍"]), state='*')
async def user_main_menu(message: types.Message, state: FSMContext):
    await message.answer("Suralar bo'limi")

    user_id = message.from_user.id
    req = requests.get(url="https://api.alquran.cloud/v1/surah").json()
    for surah in range(len(req['data'])):
        surah_list[surah] = req['data'][surah]['englishName']

    surahs = []
    for i in range(0, 19):
        surahs.append(InlineKeyboardButton(text=surah_list[i], callback_data=f'sura_{i + 1}'))
        await state.update_data(
            {'surah_pages': i}
        )
    sura_ikb = InlineKeyboardMarkup(row_width=3)
    next_btn = InlineKeyboardButton(text="➡️", callback_data='next')
    # leave_btn = InlineKeyboardButton(text="Bosh menu 🔝", callback_data='leave')
    sura_ikb.add(*surahs).add(next_btn)
    with open("handlers/images/quran_karim.jpg", 'rb') as photo:
        await bot.send_photo(chat_id=user_id, photo=photo, caption="Suralar 👇", reply_markup=sura_ikb)
    await StartCMD.surah_menu.set()


@dp.callback_query_handler(state=StartCMD.surah_menu)
async def surah_list_call(call: types.CallbackQuery, state: FSMContext):
    print(call.data)
    callback = call.data
    datas = await state.get_data()
    last_page = datas.get('surah_pages')
    user_id = call.from_user.id

    if callback == 'next':
        buttons = []
        previous_btn = InlineKeyboardButton(text="⬅️", callback_data='previous')
        # leave_btn = InlineKeyboardButton(text="Bosh menu 🔝", callback_data='leave')
        next_page_btn = InlineKeyboardMarkup(row_width=3)

        last_surah = 0
        for i in range(last_page + 1, last_page + 20):
            surah_name = surah_list[i]
            buttons.append(InlineKeyboardButton(text=surah_name, callback_data=f'sura_{i + 1}'))
            await state.update_data(
                {'surah_pages': i}
            )
            last_surah = i

        if last_surah != 113:
            next_btn = InlineKeyboardButton(text="➡️", callback_data='next')
            next_page_btn.add(*buttons).add(previous_btn, next_btn)
            await call.message.edit_caption(caption='Suralar 👇', reply_markup=next_page_btn)

            await call.answer(callback)
        else:
            next_page_btn.add(*buttons).add(previous_btn)
            await call.message.edit_caption(caption='Suralar [ sahifa oxiri ] 👇', reply_markup=next_page_btn)
            await call.answer(callback)
    elif callback == 'previous':
        buttons = []
        next_btn = InlineKeyboardButton(text="➡️", callback_data='next')
        # leave_btn = InlineKeyboardButton(text="Bosh menu 🔝", callback_data='leave')
        next_page_btn = InlineKeyboardMarkup(row_width=3)

        last_surah = 0
        for i in range(last_page, last_page - 19, -1):
            last_surah = i
        for i in range(last_surah - 19, last_surah):
            surah_name = surah_list[i]
            buttons.append(InlineKeyboardButton(text=surah_name, callback_data=f'sura_{i + 1}'))
            await state.update_data(
                {'surah_pages': i}
            )
        if last_surah != 19:
            previous_btn = InlineKeyboardButton(text="⬅️", callback_data='previous')
            next_page_btn.add(*buttons).add(previous_btn, next_btn)
            await call.message.edit_caption(caption='Suralar 👇', reply_markup=next_page_btn)
        else:
            next_page_btn.add(*buttons).add(next_btn)
            await call.message.edit_caption(caption='Suralar [ sahifa boshi ] 👇', reply_markup=next_page_btn)
        await call.answer(callback)

    elif callback.startswith('sura_') or callback.startswith('back_to_'):
        await call.message.delete()
        num_of_surah = 0
        if callback.startswith('sura_'):
            num_of_surah = callback.split('_')[1]
        elif callback.startswith('back_to_'):
            num_of_surah = callback.split('_')[2]
        await call.answer(num_of_surah)
        request = requests.get(url=f"https://api.alquran.cloud/v1/surah/{num_of_surah}").json()
        r = request['data']

        surah_number = int(r['number'])
        arab_name = r['name']
        eng_name = r['englishName']
        trans_name = r['englishNameTranslation']
        revelation = r['revelationType']
        num_of_ayah = int(r['numberOfAyahs'])

        translator = GoogleTranslator(target='uz', source='en')
        trans_name = translator.translate(trans_name)

        await state.update_data(
            {'surah_pages_sec': num_of_surah}
        )

        caption = (f"<code>🔹 <b>{surah_number}</b> - sura\n"
                   f"🔹 Sura nomi: <b>{eng_name} [ {arab_name} ]</b>\n"
                   f"🔹 Tarjimasi: <b>{trans_name}</b>\n"
                   f"🔹 Vahiy turi: <b>{revelation}</b>\n"
                   f"🔹 <b>{eng_name}</b> surasi <b>{num_of_ayah}</b> oyatdan iborat</code>\n\n"
                   f"<a href='https://t.me/R_Yusuf_Bot'>SmartCoder</a>")
        if len(caption_list) > 0:
            caption_list.clear()
            caption_list.append(caption)
        else:
            caption_list.append(caption)

        # media = [types.InputMediaPhoto(media=InputFile("handlers/images/ayah.jpg", "ayah.jpg"),
        #                                caption=caption)]
        with open("handlers/images/ayah.jpg", 'rb') as photo:
            await bot.send_photo(caption=caption, photo=photo, chat_id=call.from_user.id,
                                 reply_markup=surah_ikb())
    if callback == 'go_home':
        await call.message.delete()
        await user_main_menu(call, state)
        ayah_list.clear()
    elif callback == 'text' or callback == 'translation':
        await call.answer("Ayah page")
        await call.message.delete()
        user_id = call.from_user.id
        datas = await state.get_data()
        num_of_surah = datas.get('surah_pages_sec')

        request_text = requests.get(url=f"https://api.alquran.cloud/v1/surah/{num_of_surah}").json()
        r = request_text['data']
        print(r)
        eng_name = r['englishName']
        surah_num = r['number']
        number_of_ayah = r['numberOfAyahs']

        image = requests.get(
            url=f"https://cdn.islamic.network/quran/images/high-resolution/{surah_num}_{r['ayahs'][0]['numberInSurah']}.png"
        )
        # print(r['ayahs'][0]['sajda'])
        if str(r['ayahs'][0]['sajda']) == 'False':
            res_sajda = " emas‼️"
        else:
            res_sajda = "‼️"

        caption = (f"🔹<code>{eng_name} - surasi [ {r['ayahs'][0]['numberInSurah']} | {number_of_ayah} ]\n"
                   f"🔹Surada: {r['ayahs'][0]['numberInSurah']} - oyat\n"
                   f"🔹Quronda: {r['ayahs'][0]['number']} - oyat\n"
                   f"🔹Juz: {r['ayahs'][0]['juz']}\n"
                   f"🔹Sahifa: {r['ayahs'][0]['page']}\n"
                   f"⚠️ Ushbu oyat Sajda oyati{res_sajda}\n"
                   f"🔹Oyat matni 👇\n\n</code><code>{r['ayahs'][0]['text']}")

        control = InlineKeyboardMarkup(row_width=3)
        audio = InlineKeyboardButton(text="Audio 🎧", callback_data='audio_ayah')
        current_ayah = InlineKeyboardButton(text=f"{r['ayahs'][0]['numberInSurah']} | {number_of_ayah}",
                                            callback_data='current_ayah')
        trans = InlineKeyboardButton(text="Tarjima 📄", callback_data='translation_ayah')
        back_sura = InlineKeyboardButton(text="⬅️ Sura", callback_data=f'back_to_{surah_num}')
        back_home = InlineKeyboardButton(text="🔝 Suralar", callback_data='go_home')

        # control.add(audio, current_ayah, trans).add().add(back_sura, back_home)

        max_caption_length = 1000

        if image.status_code == 200:
            if len(caption) < max_caption_length:
                if int(r['ayahs'][0]['numberInSurah']) != number_of_ayah:
                    next_ayah = InlineKeyboardButton(text="➡️", callback_data='next_ayah')
                    control.add(audio, current_ayah, trans).add(next_ayah).add(back_sura, back_home)
                elif int(r['ayahs'][0]['numberInSurah']) > 0:
                    next_ayah = InlineKeyboardButton(text="➡️", callback_data='next_ayah')
                    previous_ayah = InlineKeyboardButton(text="⬅️", callback_data='previous_ayah')
                    control.add(audio, current_ayah, trans).add(previous_ayah, next_ayah).add(back_sura, back_home)
                await bot.send_photo(chat_id=user_id, photo=image.content, caption=f"{caption}</code>",
                                     reply_markup=control)
            else:
                caption_chunks = [caption[i:i + max_caption_length] for i in range(0, len(caption), max_caption_length)]
                part_1 = f"<code>{caption_chunks[0]}</code>"
                part_2 = f"<code>{caption_chunks[1]}</code>"
                part_1_sent = await bot.send_photo(chat_id=user_id, photo=image.content, caption=part_1)
                await bot.send_message(chat_id=user_id, text=part_2, reply_markup=control)
                part_1_id[user_id] = part_1_sent.message_id
            await state.update_data(
                {'current_ayah': r['ayahs'][0]['numberInSurah']}
            )
        else:
            await call.answer("Error code: 404")
        await state.update_data(
            {'current_surah': surah_num,
             'translation_ayah': r['ayahs'][0]['number']}
        )

    elif callback == 'next_ayah':
        await call.message.delete()
        datas = await state.get_data()
        next_ayah = datas.get('current_ayah') + 1
        num_of_surah = datas.get('surah_pages_sec')

        await call.answer(next_ayah)

        request_text = requests.get(url=f"https://api.alquran.cloud/v1/surah/{num_of_surah}").json()
        r = request_text['data']
        print(r)
        eng_name = r['englishName']
        surah_num = r['number']
        number_of_ayah = r['numberOfAyahs']

        image = requests.get(
            url=f"https://cdn.islamic.network/quran/images/high-resolution/{surah_num}_{next_ayah}.png"
        )
        ayah = next_ayah - 1
        print(r['ayahs'][ayah]['text'])
        if str(r['ayahs'][ayah]['sajda']) == 'False':
            res_sajda = " emas‼️"
        else:
            res_sajda = "‼️"

        caption = (f"🔹<code>{eng_name} - surasi [ {r['ayahs'][ayah]['numberInSurah']} | {number_of_ayah} ]\n"
                   f"🔹Surada: {r['ayahs'][ayah]['numberInSurah']} - oyat\n"
                   f"🔹Quronda: {r['ayahs'][ayah]['number']} - oyat\n"
                   f"🔹Juz: {r['ayahs'][ayah]['juz']}\n"
                   f"🔹Sahifa: {r['ayahs'][ayah]['page']}\n"
                   f"⚠️ Ushbu oyat Sajda oyati{res_sajda}\n"
                   f"🔹Oyat matni 👇\n\n</code><code>{r['ayahs'][ayah]['text']}")
        control = InlineKeyboardMarkup(row_width=3)
        audio = InlineKeyboardButton(text="Audio 🎧", callback_data='audio_ayah')
        current_ayah = InlineKeyboardButton(text=f"{r['ayahs'][ayah]['numberInSurah']} | {number_of_ayah}",
                                            callback_data='current_ayah')
        trans = InlineKeyboardButton(text="Tarjima 📄", callback_data='translation_ayah')
        back_sura = InlineKeyboardButton(text="⬅️ Sura", callback_data=f'back_to_{surah_num}')
        back_home = InlineKeyboardButton(text="🔝 Suralar", callback_data='go_home')

        max_caption_length = 1000

        if image.status_code == 200:
            if len(caption) < max_caption_length:
                if int(r['ayahs'][ayah]['numberInSurah']) == number_of_ayah:
                    previous_ayah = InlineKeyboardButton(text="⬅️", callback_data='previous_ayah')
                    control.add(audio, current_ayah, trans).add(previous_ayah).add(back_sura, back_home)
                elif int(r['ayahs'][ayah]['numberInSurah']) > 0:
                    next_ayah = InlineKeyboardButton(text="➡️", callback_data='next_ayah')
                    previous_ayah = InlineKeyboardButton(text="⬅️", callback_data='previous_ayah')
                    control.add(audio, current_ayah, trans).add(previous_ayah, next_ayah).add(back_sura, back_home)
                elif int(r['ayahs'][ayah]['numberInSurah']) != number_of_ayah:
                    next_ayah = InlineKeyboardButton(text="➡️", callback_data='next_ayah')
                    control.add(audio, current_ayah, trans).add(next_ayah).add(back_sura, back_home)
                await bot.send_photo(chat_id=user_id, photo=image.content, caption=f"{caption}</code>",
                                     reply_markup=control)
            else:
                caption_chunks = [caption[i:i + max_caption_length] for i in range(0, len(caption), max_caption_length)]
                part_1 = f"<code>{caption_chunks[0]}</code>"
                part_2 = f"<code>{caption_chunks[1]}</code>"
                part_1_sent = await bot.send_photo(chat_id=user_id, photo=image.content, caption=part_1)
                await bot.send_message(chat_id=user_id, text=part_2, reply_markup=control)
                part_1_id[user_id] = part_1_sent.message_id
            await state.update_data(
                {'current_ayah': r['ayahs'][ayah]['numberInSurah']}
            )
        else:
            await call.answer("Error code: 404")
        await state.update_data(
            {'current_surah': surah_num,
             'translation_ayah': r['ayahs'][ayah]['number']}
        )

    elif callback == 'previous_ayah':
        datas = await state.get_data()
        current_ayah = datas.get('current_ayah') - 1
        await call.answer(current_ayah)
        await call.message.delete()
        num_of_surah = datas.get('surah_pages_sec')

        request_text = requests.get(url=f"https://api.alquran.cloud/v1/surah/{num_of_surah}").json()
        r = request_text['data']
        print(r)
        eng_name = r['englishName']
        surah_num = r['number']
        number_of_ayah = r['numberOfAyahs']

        image = requests.get(
            url=f"https://cdn.islamic.network/quran/images/high-resolution/{surah_num}_{current_ayah}.png"
        )
        ayah = current_ayah - 1

        if str(r['ayahs'][ayah]['sajda']) == 'False':
            res_sajda = " emas‼️"
        else:
            res_sajda = "‼️"

        caption = (f"🔹<code>{eng_name} - surasi [ {r['ayahs'][ayah]['numberInSurah']} | {number_of_ayah} ]\n"
                   f"🔹Surada: {r['ayahs'][ayah]['numberInSurah']} - oyat\n"
                   f"🔹Quronda: {r['ayahs'][ayah]['number']} - oyat\n"
                   f"🔹Juz: {r['ayahs'][ayah]['juz']}\n"
                   f"🔹Sahifa: {r['ayahs'][ayah]['page']}\n"
                   f"⚠️ Ushbu oyat Sajda oyati{res_sajda}\n"
                   f"🔹Oyat matni 👇\n\n</code><code>{r['ayahs'][ayah]['text']}")

        control = InlineKeyboardMarkup(row_width=3)
        audio = InlineKeyboardButton(text="Audio 🎧", callback_data='audio_ayah')
        current_ayah = InlineKeyboardButton(text=f"{r['ayahs'][ayah]['numberInSurah']} | {number_of_ayah}",
                                            callback_data='current_ayah')

        trans = InlineKeyboardButton(text="Tarjima 📄", callback_data='translation_ayah')
        back_sura = InlineKeyboardButton(text="⬅️ Sura", callback_data=f'back_to_{surah_num}')
        back_home = InlineKeyboardButton(text="🔝 Suralar", callback_data='go_home')

        max_caption_length = 1000

        if image.status_code == 200:
            if len(caption) < max_caption_length:
                if int(r['ayahs'][ayah]['numberInSurah']) == 1:
                    next_ayah = InlineKeyboardButton(text="➡️", callback_data='next_ayah')
                    control.add(audio, current_ayah, trans).add(next_ayah).add(back_sura, back_home)
                elif int(r['ayahs'][ayah]['numberInSurah']) > 1:
                    next_ayah = InlineKeyboardButton(text="➡️", callback_data='next_ayah')
                    previous_ayah = InlineKeyboardButton(text="⬅️", callback_data='previous_ayah')
                    control.add(audio, current_ayah, trans).add(previous_ayah, next_ayah).add(back_sura, back_home)
                await bot.send_photo(chat_id=user_id, photo=image.content, caption=f"{caption}</code>",
                                     reply_markup=control)
            else:
                caption_chunks = [caption[i:i + max_caption_length] for i in range(0, len(caption), max_caption_length)]
                part_1 = f"<code>{caption_chunks[0]}</code>"
                part_2 = f"<code>{caption_chunks[1]}</code>"
                part_1_sent = await bot.send_photo(chat_id=user_id, photo=image.content, caption=part_1)
                await bot.send_message(chat_id=user_id, text=part_2, reply_markup=control)
                part_1_id[user_id] = part_1_sent.message_id
            await state.update_data(
                {'current_ayah': r['ayahs'][ayah]['numberInSurah']}
            )
        else:
            await call.answer("Error code: 404")
        await state.update_data(
            {'current_surah': surah_num,
             'translation_ayah': r['ayahs'][ayah]['number']}
        )

    elif callback == 'audio_ayah':
        ayahs_data = await state.get_data()
        current_ayah = ayahs_data.get('current_ayah')
        current_surah = ayahs_data.get('current_surah')
        await call.answer(current_ayah)
        signature = '<a href="https://t.me/R_Yusuf_Bot">Created by SmartCoder 🧑‍💻</a>'

        req_audio = requests.get(url=f"https://api.alquran.cloud/v1/ayah/{current_surah}:{current_ayah}/ar.alafasy").json()
        audio = req_audio['data']['audio']
        await bot.send_audio(chat_id=call.from_user.id, audio=audio, caption=signature)

    elif callback == 'translation_ayah':
        await call.answer("Tarjima")
        translation_data = await state.get_data()
        current_ayah = translation_data.get('translation_ayah')
        req_translation = requests.get(
            url="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/uzb-muhammadsodikmu.json").json()
        trans = req_translation['quran'][current_ayah - 1]['text']
        chapter = req_translation['quran'][current_ayah - 1]['chapter']
        verse = req_translation['quran'][current_ayah - 1]['verse']
        signature = '<a href="https://t.me/R_Yusuf_Bot">Created by SmartCoder 🧑‍💻</a>'

        # less_btn = InlineKeyboardMarkup(inline_keyboard=[
        #     [InlineKeyboardButton(text="➖", callback_data='less_btn')]
        # ])
        text = (f"| {chapter} - sura | {verse} - oyat | {current_ayah} - oyat |"
                f"\nTarjima va tafsiri 👇\n\n<code>{trans}</code>")
        text += f"\n\n{signature}"

        share_button = types.InlineKeyboardButton(
            "Do'stlarga ulashish ⤴️", switch_inline_query=f'👈 ushbu botga kiring va men bilan Quronni yod oling!\n\n'
                                                       f'{text}'
        )
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(share_button)

        await call.message.answer(text=text, parse_mode="HTML", reply_markup=keyboard)
    # elif callback == 'less_btn':
    #     cropped_text = str(call.message.text).split('Tarjima va tafsiri 👇')[0]
    #     more_btn = InlineKeyboardMarkup(inline_keyboard=[
    #         [InlineKeyboardButton(text="➕", callback_data='more_btn')]
    #     ])
    #     await call.message.edit_text(text=cropped_text, reply_markup=more_btn)
    # elif callback == 'more_btn':
    #     get_nums_of_ayah = str(call.message.text).split(' ')
    #     surah = get_nums_of_ayah[1]
    #     ayah = get_nums_of_ayah[5]
    #     quran_ayah = get_nums_of_ayah[9]
    #     translation_data = await state.get_data()
    #     current_ayah = translation_data.get('translation_ayah')
    #     req_translation = requests.get(
    #         url="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/uzb-muhammadsodikmu.json").json()
    #     trans = req_translation['quran'][current_ayah - 1]['text']
    #     less_btn = InlineKeyboardMarkup(inline_keyboard=[
    #         [InlineKeyboardButton(text="➖", callback_data='less_btn')]
    #     ])
    #     await call.message.edit_text(f"| {surah} - sura | {ayah} - oyat | {quran_ayah} - oyat |"
    #                                  f"\nTarjima va tafsiri 👇\n\n<code>{trans}</code>", parse_mode="HTML",
    #                                  reply_markup=less_btn)
    elif callback == 'current_ayah':
        first_line = str(call.message.caption).split('\n')[0]
        await call.answer(first_line)

    elif callback == 'audio_surah':
        await call.answer("Audio")
        datas = await state.get_data()
        surah = datas.get('surah_pages_sec')
        surah = int(surah) + 2
        user_id = call.from_user.id

        audio = f"https://t.me/Quran_By_Ayah/{surah}"
        signature = '<a href="https://t.me/R_Yusuf_Bot">Created by SmartCoder 🧑‍💻</a>'
        await bot.send_audio(chat_id=user_id, audio=audio, caption=signature, parse_mode="HTML")
    elif callback == 'ayah':
        await call.message.delete()
        await call.answer("Ayahs")
        datas = await state.get_data()
        surah = datas.get('surah_pages_sec')
        req_ayahs = requests.get(f"https://api.alquran.cloud/v1/surah/{surah}.").json()
        btns = []
        for ayahs in range(req_ayahs['data']['numberOfAyahs']):
            btns.append(InlineKeyboardButton(text=f"{ayahs + 1}", callback_data=f'ayah_{surah}_{ayahs + 1}'))
        ayah_btns = InlineKeyboardMarkup(row_width=8)

        sura_btn = InlineKeyboardButton(text="⬅️ sura", callback_data=f"back_to_{surah}")
        home_btn = InlineKeyboardButton(text="🔝 Suralar", callback_data="go_home")
        if int(req_ayahs['data']['numberOfAyahs']) < 48:
            ayah_btns.add(*btns).add(sura_btn, home_btn)
            with open("handlers/images/Ayahs.png", 'rb') as photo:
                await bot.send_photo(photo=photo, caption="Ayahs 👇", reply_markup=ayah_btns,
                                     chat_id=call.from_user.id)
        else:
            for btn in range(0, 48):
                ayah_btns.insert(btns[btn])
                last_btn = btn
                await state.update_data(
                    {'last_btn': last_btn + 1}
                )
            next_page_ayah = InlineKeyboardButton(text="➡️", callback_data="next_page_ayahs")
            ayah_btns.add(next_page_ayah).add(sura_btn, home_btn)
            with open("handlers/images/Ayahs.png", 'rb') as photo:
                await bot.send_photo(photo=photo, caption="Ayahs 👇", reply_markup=ayah_btns,
                                     chat_id=call.from_user.id)
    elif callback == 'next_page_ayahs':
        await call.message.delete()
        datas = await state.get_data()
        surah = datas.get('surah_pages_sec')
        next_page_data = await state.get_data()
        last_btn = next_page_data.get('last_btn')
        current_surah = next_page_data.get('surah_pages_sec')
        req_ayahs = requests.get(f"https://api.alquran.cloud/v1/surah/{current_surah}").json()
        total_ayahs = req_ayahs['data']['numberOfAyahs']

        ayah_btns = InlineKeyboardMarkup(row_width=8)
        sura_btn = InlineKeyboardButton(text="⬅️ Сура", callback_data=f"back_to_{current_surah}")
        home_btn = InlineKeyboardButton(text="🔝 Суры", callback_data="go_home")

        # Рассчитать диапазон для следующей страницы кнопок аятов
        start_btn = last_btn
        end_btn = min(last_btn + 48, total_ayahs)

        btns = []
        for btn in range(start_btn, end_btn):
            btn_text = str(btn + 1)
            btns.append(InlineKeyboardButton(text=btn_text, callback_data=f"ayah_{surah}_{btn + 1}"))

        ayah_btns.add(*btns)

        if end_btn < total_ayahs:
            next_page_ayah = InlineKeyboardButton(text="➡️", callback_data="next_page_ayahs")
            ayah_btns.add(next_page_ayah)

        ayah_btns.add(sura_btn, home_btn)

        with open("handlers/images/Ayahs.png", 'rb') as photo:
            await bot.send_photo(photo=photo, caption="Ayahs 👇", reply_markup=ayah_btns,
                                 chat_id=call.from_user.id)

        await state.update_data({'last_btn': last_btn + 48})

    elif callback.startswith('ayah_'):
        surah_num = callback.split('_')[1]
        ayah_num = callback.split('_')[2]
        await call.answer(f"{surah_num} / {ayah_num}")
        # print(surah_num, ayah_num)
        request_ayah = requests.get(url=f"https://api.alquran.cloud/v1/ayah/{surah_num}:{ayah_num}").json()
        req_translation = requests.get(
            url="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/uzb-muhammadsodikmu.json").json()
        print(request_ayah['data']['text'])

        eng_name = request_ayah['data']['surah']['englishName']
        number_of_ayah = request_ayah['data']['surah']['numberOfAyahs']

        if str(request_ayah['data']['sajda']) == 'False':
            res_sajda = " emas‼️"
        else:
            res_sajda = "‼️"

        caption = (f"🔹<code>{eng_name} - surasi [ {request_ayah['data']['numberInSurah']} | {number_of_ayah} ]\n"
                   f"🔹Surada: {request_ayah['data']['numberInSurah']} - oyat\n"
                   f"🔹Quronda: {request_ayah['data']['number']} - oyat\n"
                   f"🔹Juz: {request_ayah['data']['juz']}\n"
                   f"🔹Sahifa: {request_ayah['data']['page']}\n"
                   f"⚠️ Ushbu oyat Sajda oyati{res_sajda}\n"
                   f"🔹Oyat matni 👇\n\n</code><code>{request_ayah['data']['text']}</code>")
        # await call.message.answer(caption)
        req_audio = requests.get(
            url=f"https://api.alquran.cloud/v1/ayah/{surah_num}:{ayah_num}/ar.alafasy").json()
        audio = req_audio['data']['audio']
        await bot.send_audio(chat_id=call.from_user.id, audio=audio, caption=caption)

        req_translation = requests.get(
            url="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/uzb-muhammadsodikmu.json").json()
        trans = req_translation['quran'][int(request_ayah['data']['number']) - 1]['text']
        image = requests.get(
            url=f"https://cdn.islamic.network/quran/images/high-resolution/{surah_num}_{ayah_num}.png"
        )
        await bot.send_photo(chat_id=call.from_user.id, photo=image.content, caption=f"<code>{trans}</code>", parse_mode="HTML")
    else:
        await call.answer("Xabar eskirgan")
