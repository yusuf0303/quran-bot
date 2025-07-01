import requests

from Suralar.API_lar import QURAN_API, TRANSLATION_API
from Suralar.menu_button import logger

def show_specific_ayah(query, context):
    """Show specific ayah details"""
    try:
        surah_num = query.data.split('_')[1]#data malumotlari 2 eliment sura boladi indexsi 1 ga teng
        #yani API dan kelayotgan json formatda boladi shunda 2- eliment sura
        ayah_num = query.data.split('_')[2]#3- eliment oytlar endix 2 ga teng
        query.answer(f"Surah {surah_num}, Ayah {ayah_num}")
        datas=context.user_data
        datas['previous_state'] = 'ayah_detail'

        request_ayah = requests.get(url=f"{QURAN_API}/ayah/{surah_num}:{ayah_num}").json()
        req_translation = requests.get(url=TRANSLATION_API).json()

        surah_data = request_ayah['data']['surah']
        ayah_data = request_ayah['data']
        eng_name = surah_data['englishName']
        number_of_ayah = surah_data['numberOfAyahs']
        res_sajda = " emas‼️" if str(ayah_data['sajda']) == 'False' else "‼️"

        caption = (f"🔹<code>{eng_name} - surasi [ {ayah_data['numberInSurah']} | {number_of_ayah} ]\n"
                   f"🔹Surada: {ayah_data['numberInSurah']} - oyat\n"
                   f"🔹Quronda: {ayah_data['number']} - oyat\n"
                   f"🔹Juz: {ayah_data['juz']}\n"
                   f"🔹Sahifa: {ayah_data['page']}\n"
                   f"⚠️ Ushbu oyat Sajda oyati{res_sajda}\n"
                   f"🔹Oyat matni 👇\n</code><code>{ayah_data['text']}</code>"
                   
                   
                   "📖 Qur'oni karim oyatlarining ma'nolari\n"
                   "Shayx Muhammad Sodiq Muhammad Yusuf hazratlarining "
                   "tarjimalari asosida keltirilgan.")



        req_audio = requests.get(
            url=f"{QURAN_API}/ayah/{surah_num}:{ayah_num}/ar.alafasy"
        ).json()

        audio = req_audio['data'].get('audio')
        if audio:
            context.bot.send_audio(
                chat_id=query.from_user.id,
                audio=audio,
                caption=caption,
                parse_mode="HTML"
            )
        else:
            query.answer("⚠️ Audio topilmadi")

        trans = req_translation['quran'][int(ayah_data['number']) - 1]['text']

        image_url = f"https://cdn.islamic.network/quran/images/high-resolution/{surah_num}_{ayah_num}.png"
        image = requests.get(image_url)

        if image.status_code == 200:
            context.bot.send_photo(

                chat_id=query.from_user.id,
                photo=image.content,
                caption=f"<code>{trans}</code>",
                parse_mode="HTML"

            )
        else:
            query.answer("⚠️ Oyat rasmi topilmadi")

        context.user_data['current_ayah'] = int(ayah_num)
        context.user_data['current_surah'] = int(surah_num)
        context.user_data['translation_ayah'] = ayah_data['number']

    except Exception as e:
        logger.error(f"Error showing specific ayah: {e}")
        query.answer("⚠️ Oyat yuklanmadi")
