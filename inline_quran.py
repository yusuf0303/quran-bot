import requests
from telegram import (
    InlineQueryResultArticle,
    InlineQueryResultAudio,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import InlineQueryHandler
import uuid
from uuid import uuid4

from SURAH_MAPPING import SURAH_MAP

BASE_URL = "https://api.alquran.cloud/v1/"


def inline_query_handler(update, context):
    query = update.inline_query.query.strip().lower()
    results = []

    if not query:
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🔎 Qidirish uchun quyidagi kalit so'zlardan foydalaning",
                description="Sura nomi, sura nomi + oyat raqami, sajda",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "⚠️ Qidirish uchun quyidagi kalit so'zlardan foydalaning \n\n"
                        "Sura nomi, sura nomi + oyat raqami, sajda\n"
                        "Masalan: <i>Fotiha</i>, <i>Baqara 255</i>, <i>Sajda</i>"
                    ),
                    parse_mode="HTML"
                )
            )
        )
        update.inline_query.answer(results, cache_time=1)
        return

    if query.startswith("quiz_"):
        parts = query.split("_")
        if len(parts) >= 2:
            quiz_id = query.replace("quiz_", "", 1)
            # Default display if it's a new ID or settings
            display_count = parts[2] if len(parts) >= 3 else "?"
            display_juz = parts[1].replace("-", ", ") if len(parts) >= 2 else "?"
            display_time = parts[3] if len(parts) >= 4 else "?"
            
            bot_username = context.bot.username
            group_deep_link = f"https://t.me/{bot_username}?startgroup=quiz_{quiz_id}"
            private_deep_link = f"https://t.me/{bot_username}?start=quiz_{quiz_id}"
            
            results.append(
                InlineQueryResultArticle(
                    id=uuid4().hex,
                    title=f"🚀 Savol-Javob (Quiz): {display_count} ta savol",
                    description=f"Juzlar: {display_juz} | Vaqt: {display_time} sek",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"📖 **Yangi Savol-Javob (Quiz)**\n\n"
                            f"📖 **Juzlar:** {display_juz}\n"
                            f"❓ **Savollar soni:** {display_count} ta\n"
                            f"⏳ **Har bir savolga:** {display_time} sekund\n\n"
                            f"Testni boshlash uchun pastdagi tugmani bosing 👇"
                        ),
                        parse_mode="Markdown"
                    ),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🏁 Shaxsiyda boshlash", url=private_deep_link)],
                        [InlineKeyboardButton("👥 Guruhda boshlash", url=group_deep_link)],
                        [InlineKeyboardButton("📤 Ulashish", switch_inline_query=f"quiz_{quiz_id}")]
                    ])
                )
            )
            update.inline_query.answer(results, cache_time=1)
            return

    if query.startswith("ramadan_r"):
        user_id = query.replace("ramadan_r", "")
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=r{user_id}"
        
        invitation_text = (
            f"Assalomu alaykum! 🌙\n\n"
            f"Sizni KalomUz botidagi <b>Ramazon konkursiga</b> taklif qilaman! 🏆\n\n"
            f"Konkursda qatnashib, qimmatbaho kitoblar to'plamini yutib olishingiz mumkin. 🎁\n\n"
            f"Ro'yxatdan o'tish uchun ushbu havolani bosing: {ref_link}"
        )
        
        results.append(
            InlineQueryResultArticle(
                id=uuid4().hex,
                title="🌙 Ramazon Konkursiga taklifnoma",
                description="Do'stlaringizni taklif qiling va ballar to'plang!",
                thumb_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6f9Y_NqV5F_0_GZQ_XZy_8H_J_0_0_GZQ_XZy_8H_J_0&s",
                input_message_content=InputTextMessageContent(
                    message_text=invitation_text,
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏆 Konkursda qatnashish", url=ref_link)]
                ])
            )
        )
        update.inline_query.answer(results, cache_time=1)
        return

    parts = query.split()
    surah_name_part = parts[0]
    ayah_num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

    # 🔹 Qisman mos keladigan suralarni topish
    matching_surahs = [
        (name, num) for name, num in SURAH_MAP.items()
        if surah_name_part in name.lower()
    ]

    # Agar hech qanday sura topilmasa
    if not matching_surahs and surah_name_part != "sajda":
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"❌ {query.capitalize()} ga aloqador natijalar topilmadi",
                description="Sura nomini to'g'rilab qayta qidirib ko'ring",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "⚠️ Qidirish uchun quyidagi kalit so'zlardan foydalaning \n\n"
                        "Sura nomi, sura nomi + oyat raqami, sajda\n"
                        "Masalan: <i>Fotiha</i>, <i>Baqara 255</i>, <i>Sajda</i>"
                    ),
                    parse_mode="HTML"
                )
            )
        )
        update.inline_query.answer(results, cache_time=1)
        return

    # 🔹 Agar faqat qidirish bo‘lsa
    if len(parts) == 1 and query != "sajda":
        for name, num in matching_surahs:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=name.capitalize(),
                    description=f"{name.capitalize()} surasi",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"📖 <b>{name.capitalize()}</b> surasi haqida ma’lumot olish uchun "
                            f"oyat raqamini ham kiriting.\n\nMasalan: <code>{name} 5</code>"
                        ),
                        parse_mode="HTML"
                    )
                )
            )

            # 🔹 Butun sura (arabcha)
            resp = requests.get(f"{BASE_URL}surah/{num}")
            if resp.status_code == 200:
                data = resp.json()
                audio_url = f"https://t.me/Quran_By_Ayah/{num + 2}"
                if data["status"] == "OK":
                    surah = data["data"]
                    ayahs = [a["text"] for a in surah["ayahs"]]
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title=surah["englishName"],
                            description=f"{surah['name']} ({len(ayahs)} oyat)",
                            input_message_content=InputTextMessageContent(
                                message_text=(
                                    f"📖 {surah['name']} ({surah['englishName']})\n\n"
                                    f"{ayahs[0]} ...\n\n"
                                    f"🎧[{surah['englishName']} surasini tinglash]({audio_url})"
                                ),
                                parse_mode="Markdown"
                            )
                        )
                    )
        results = results[:50]
        update.inline_query.answer(results, cache_time=1)
        return

    # 🔹 Agar oyat raqami ham kiritilgan bo‘lsa
    if ayah_num:
        surah_name, surah_num = matching_surahs[0]

        # Oyatlar sonini tekshirish
        resp_surah = requests.get(f"{BASE_URL}surah/{surah_num}")
        if resp_surah.status_code == 200:
            surah_info = resp_surah.json()["data"]
            total_ayahs = surah_info["numberOfAyahs"]

            if ayah_num > total_ayahs:
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        title="❌ Noto‘g‘ri oyat raqami",
                        description=f"{surah_info['englishName']} surasi {total_ayahs} ta oyatdan iborat.",
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                f"⚠️ <b>{surah_info['name']}</b> surasi {total_ayahs} oyatdan iborat.\n"
                                f"Siz {ayah_num}-raqamni kiritdingiz, lekin u mavjud emas."
                            ),
                            parse_mode="HTML"
                        )
                    )
                )
                results = results[:50]
                update.inline_query.answer(results, cache_time=1)
                return

        # Arabcha oyat + audio
        resp = requests.get(f"{BASE_URL}ayah/{surah_num}:{ayah_num}/ar.alafasy")
        if resp.status_code == 200:
            data = resp.json()
            if data["status"] == "OK":
                ayah = data["data"]
                caption = (
                    f"📖 <b>{ayah['surah']['name']}</b> ({ayah['surah']['englishName']})\n"
                    f"🕌 <i>Oyat {ayah['numberInSurah']}</i>\n\n"
                    f"✨ {ayah['text']}\n\n"
                    f"@KalomUzBot"
                )
                results.append(
                    InlineQueryResultAudio(
                        id=str(uuid.uuid4()),
                        audio_url=ayah.get("audio"),
                        title=f"{surah_name.capitalize()} {ayah_num}-oyat (Arabcha)",
                        performer="Mishary Rashid Alafasy",
                        caption=caption,
                        parse_mode="HTML"
                    )
                )

        # O‘zbekcha tarjima
        resp_tr = requests.get(f"{BASE_URL}ayah/{surah_num}:{ayah_num}/uz.sodik")
        if resp_tr.status_code == 200:
            data_tr = resp_tr.json()
            if data_tr["status"] == "OK":
                ayah_tr = data_tr["data"]
                message_text = (
                    f"📖 <b>{ayah_tr['surah']['name']}</b> ({ayah_tr['surah']['englishName']})\n"
                    f"🕌 <i>Oyat {ayah_tr['numberInSurah']} tarjimasi</i>\n\n"
                    f"✨ {ayah_tr['text']}\n\n"
                    f"@KalomUzBot"
                )
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        title=f"{surah_name.capitalize()} {ayah_num}-oyat (Tarjima)",
                        description=ayah_tr["text"][:50] + "..." if len(ayah_tr["text"]) > 50 else ayah_tr["text"],
                        input_message_content=InputTextMessageContent(
                            message_text=message_text,
                            parse_mode="HTML"
                        )
                    )
                )

    # 🔹 Sajda oyatlari (audio bilan)
    if query.split()[0].lower() == "sajda":
        resp = requests.get(f"{BASE_URL}sajda/quran-uthmani")
        if resp.status_code == 200:
            data = resp.json()
            if data["status"] == "OK":
                counter = 0
                for item in data["data"]["ayahs"]:
                    surah_num = item["surah"]["number"]
                    ayah_num = item["numberInSurah"]
                    ayah_text = item["text"]
                    counter += 1

                    audio_resp = requests.get(f"{BASE_URL}ayah/{surah_num}:{ayah_num}/ar.alafasy")
                    audio_url = None
                    if audio_resp.status_code == 200 and audio_resp.json().get("status") == "OK":
                        audio_url = audio_resp.json()["data"].get("audio")

                    caption = (
                        f"📖 <b>{item['surah']['name']}</b> ({item['surah']['englishName']})\n"
                        f"🕌 <i>Sajda oyati — {ayah_num}</i>\n\n"
                        f"{ayah_text}"
                    )

                    if audio_url:
                        results.append(
                            InlineQueryResultAudio(
                                id=str(uuid.uuid4()),
                                audio_url=audio_url,
                                title=f"{counter}. {item['surah']['englishName']} {ayah_num}-oyat (Sajda)",
                                performer="Mishary Rashid Alafasy",
                                caption=caption,
                                parse_mode="HTML"
                            )
                        )
                    else:
                        results.append(
                            InlineQueryResultArticle(
                                id=str(uuid.uuid4()),
                                title=f"{counter}. {item['surah']['englishName']} {ayah_num}-oyat (Sajda)",
                                description=ayah_text[:50] + "..." if len(ayah_text) > 50 else ayah_text,
                                input_message_content=InputTextMessageContent(
                                    message_text=caption,
                                    parse_mode="HTML"
                                )
                            )
                        )

    results = results[:50]
    update.inline_query.answer(results, cache_time=1)


def setup_inline_handlers(dp):
    dp.add_handler(InlineQueryHandler(inline_query_handler))
