from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, MessageHandler, Filters
import random
import requests
import logging
from Suralar.button_handler import button_handler
from Suralar.menu_button import main_buttons
from Suralarni_toping.surahs import SURAH_NAMES
from Suralarni_toping.database import init_db, register_user, update_user_stats, get_user_stats, get_top_10_users, \
    get_user_position

init_db()


KANAL_ID = "@Smart_Coders_Uz"
KANAL_LINK = "https://t.me/+4su6TsB0ioQwYmI6"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class OyatOyini:
    def __init__(self):
        self.joriy_oyat = None
        self.oxirgi_juz = None
        self.last_audio_message_id = None # Added to store the audio message ID


def kanalga_azo_tekshirish(user_id: int, context: CallbackContext) -> bool:
    try:
        azo = context.bot.get_chat_member(chat_id=KANAL_ID, user_id=user_id)
        return azo.status in ['member', 'administrator', 'creator', 'owner', 'admin']
    except Exception as e:
        logger.error(f"Kanal a'zoligini tekshirishda xato: {e}")
        return False


def oyat_topish(update: Update, context: CallbackContext):

    user = update.message.from_user if update.message else update.callback_query.from_user
    register_user(user)
    logger.info(f"Foydalanuvchi {user.first_name} o'yinni boshladi")

    if 'oyat_oyini' not in context.user_data:
        context.user_data['oyat_oyini'] = OyatOyini()

    tugmalar = [
        [InlineKeyboardButton("🎮 O'yinni boshlash", callback_data="oyinni_boshlash")],
        [InlineKeyboardButton("📊 Mening natijalarim", callback_data="mening_natijalarim")],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data="bosh_menyu")]
    ]

    try:
        if update.message:
            update.message.reply_text(
                f"Assalomu alaykum {user.first_name}!\n\n"
                "«Qaysi suradan?» o'yiniga xush kelibsiz!\n"
                "Berilgan oyat qaysi suradan olinganligini topishingiz kerak bo'ladi.\n\n"
                "O'yinni boshlash uchun quyidagi tugmalardan foydalaning:",
                reply_markup=InlineKeyboardMarkup(tugmalar))
        else:
            update.callback_query.edit_message_text(
                f"Assalomu alaykum {user.first_name}!\n\n"
                "«Qaysi suradan?» o'yiniga xush kelibsiz!\n"
                "Berilgan oyat qaysi suradan olinganligini topishingiz kerak bo'ladi.\n\n"
                "O'yinni boshlash uchun quyidagi tugmalardan foydalaning:",
                reply_markup=InlineKeyboardMarkup(tugmalar))
    except Exception as e:
        logger.error(f"Xato: {e}")
        context.bot.send_message(
            chat_id=user.id,
            text=f"Assalomu alaykum {user.first_name}!\n\n"
                 "«Qaysi suradan?» o'yiniga xush kelibsiz!\n"
                 "Berilgan oyat qaysi suradan olinganligini topishingiz kerak bo'ladi.\n\n"
                 "O'yinni boshlash uchun quyidagi tugmalardan foydalaning:",
            reply_markup=InlineKeyboardMarkup(tugmalar))


def kanal_tekshirib_oynash(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    if kanalga_azo_tekshirish(user_id, context):
        asl_oynani_boshlash(update, context)
    else:
        tugmalar = [
            [InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="kanalni_tekshirish")],
            [InlineKeyboardButton("📢 Kanalga kirish", url=KANAL_LINK)]
        ]

        try:
            query.edit_message_text(
                text=f"⚠️ O'yinni davom ettirish uchun quyidagi kanalga a'zo bo'lishingiz kerak:\n\n"
                     f"{KANAL_LINK}\n\n"
                     "Kanalga a'zo bo'lganingizdan so'ng «✅ A'zo bo'ldim» tugmasini bosing.",
                reply_markup=InlineKeyboardMarkup(tugmalar))
        except Exception as e:
            context.bot.send_message(
                chat_id=user_id,
                text=f"⚠️ O'yinni davom ettirish uchun quyidagi kanalga a'zo bo'lishingiz kerak:\n\n"
                     f"{KANAL_LINK}\n\n"
                     "Kanalga a'zo bo'lganingizdan so'ng «✅ A'zo bo'ldim» tugmasini bosing.",
                reply_markup=InlineKeyboardMarkup(tugmalar)
            )


def asl_oynani_boshlash(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if 'oyat_oyini' not in context.user_data:
        context.user_data['oyat_oyini'] = OyatOyini()

    tugmalar = []
    for i in range(0, 30, 5):
        qator = [
            InlineKeyboardButton(f"Juz {j + 1}", callback_data=f"juz_{j + 1}")
            for j in range(i, min(i + 5, 30))
        ]
        tugmalar.append(qator)

    tugmalar.extend([
        [InlineKeyboardButton("🔄 Tasodifiy juz", callback_data="juz_tasodifiy")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="oyat_topish")]
    ])

    try:
        try:
            query.edit_message_text(
                text="Iltimos, o'yin uchun juz tanlang:\nQur'on 30 juzdan iborat",
                reply_markup=InlineKeyboardMarkup(tugmalar)
            )
        except Exception as edit_error:
            logger.warning(f"Xabarni o'zgartirib bo'lmadi, yangi xabar yuboriladi: {edit_error}")
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Iltimos, o'yin uchun juz tanlang:\nQur'on 30 juzdan iborat",
                reply_markup=InlineKeyboardMarkup(tugmalar)
            )
            try:
                context.bot.delete_message(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id
                )
            except Exception as delete_error:
                logger.warning(f"Eski xabarni o'chirib bo'lmadi: {delete_error}")

    except Exception as e:
        logger.error(f"Xato: {e}")
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        )


def juz_tanlash(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    try:
        if query.data == "juz_tasodifiy":
            tanlangan_juz = random.randint(1, 30)
        else:
            tanlangan_juz = int(query.data.split("_")[1])

        context.user_data['oyat_oyini'].oxirgi_juz = tanlangan_juz
        javob = requests.get(
            f"https://api.alquran.cloud/v1/juz/{tanlangan_juz}/ar.alafasy",
            timeout=10
        )
        javob.raise_for_status()

        ma_lumot = javob.json()
        oyatlar = ma_lumot['data']['ayahs']

        if not oyatlar:
            raise ValueError("Tanlangan juzda oyat topilmadi")

        tasodifiy_oyat = random.choice(oyatlar)
        context.user_data['oyat_oyini'].joriy_oyat = tasodifiy_oyat

        oyat_savolini_korsatish(update, context, tasodifiy_oyat)

    except requests.exceptions.RequestException as e:
        logger.error(f"API xatosi: {e}")
        query.edit_message_text("⚠️ Qur'on ma'lumotlarini yuklab bo'lmadi. Iltimos, keyinroq urinib ko'ring.")
    except Exception as e:
        logger.error(f"Xato: {e}")
        query.edit_message_text("⚠️ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


def oyat_savolini_korsatish(update: Update, context: CallbackContext, oyat: dict):
    query = update.callback_query
    chat_id = query.message.chat_id
    oyat_oyini_instance = context.user_data['oyat_oyini']

    # Delete previous audio if it exists
    if oyat_oyini_instance.last_audio_message_id:
        try:
            context.bot.delete_message(
                chat_id=chat_id,
                message_id=oyat_oyini_instance.last_audio_message_id
            )
            oyat_oyini_instance.last_audio_message_id = None # Clear the ID after deletion
        except Exception as e:
            logger.warning(f"Oldingi audio xabarini o'chirishda xato: {e}")


    try:
        togri_sura_raqami = oyat['surah']['number']
        togri_sura = next(s for s in SURAH_NAMES if s['number'] == togri_sura_raqami)
        joriy_oyat_raqami = oyat['numberInSurah']

        variantlar = [(togri_sura, joriy_oyat_raqami)]
        while len(variantlar) < 4:
            tasodifiy_sura = random.choice([s for s in SURAH_NAMES if s['number'] != togri_sura_raqami])
            # To ensure valid ayah numbers, you'd ideally need the max ayah number for each surah
            # For simplicity, we'll keep the current logic but be aware of its limitations
            tasodifiy_oyat = random.randint(1, 286)
            if (tasodifiy_sura, tasodifiy_oyat) not in variantlar:
                variantlar.append((tasodifiy_sura, tasodifiy_oyat))

        random.shuffle(variantlar)

        tugmalar = []
        for sura, oyat_raqami in variantlar:
            tugma_matni = f"{sura['name']} surasi ➡ {oyat_raqami}-oyat [{sura['arabic']}]"
            tugmalar.append([InlineKeyboardButton(tugma_matni, callback_data=f"javob_{sura['number']}_{oyat_raqami}")])

        tugmalar.append([InlineKeyboardButton("🔙 Orqaga", callback_data="oyinni_boshlash")])

        try:
            context.bot.delete_message(
                chat_id=chat_id,
                message_id=query.message.message_id
            )
        except Exception as e:
            logger.error(f"Eski xabarni o'chirishda xato: {e}")

        # Send Photo (if available)
        try:
            rasm_manzili = f"https://cdn.islamic.network/quran/images/high-resolution/{togri_sura_raqami}_{joriy_oyat_raqami}.png"
            context.bot.send_photo(
                chat_id=chat_id,
                photo=rasm_manzili,
                caption=f"<code>{oyat['text']}</code>\n\n<b>❓ Quyidagi oyat qaysi suradan olingan?</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(tugmalar)
            )
        except Exception as e:
            logger.error(f"Rasm yuborishda xato: {e}")
            context.bot.send_message(
                chat_id=chat_id,
                text=f"<code>{oyat['text']}</code>\n\n<b>❓ Quyidagi oyat qaysi suradan olingan?</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(tugmalar)
            )

        # Send Audio and store its message_id
        try:
            audio_manzili = oyat.get('audio')
            if audio_manzili:
                sent_audio = context.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio_manzili,
                    parse_mode="HTML"
                )
                oyat_oyini_instance.last_audio_message_id = sent_audio.message_id
        except Exception as e:
            logger.error(f"Audio yuborishda xato: {e}")

    except Exception as e:
        logger.error(f"Savolni ko'rsatishda xato: {e}")
        context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Savolni tayyorlashda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        )


def javobni_tekshirish(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id
    oyat_oyini_instance = context.user_data['oyat_oyini']

    # Delete the audio message from the previous round
    if oyat_oyini_instance.last_audio_message_id:
        try:
            context.bot.delete_message(
                chat_id=chat_id,
                message_id=oyat_oyini_instance.last_audio_message_id
            )
            oyat_oyini_instance.last_audio_message_id = None # Clear the ID after deletion
        except Exception as e:
            logger.warning(f"Audio xabarini o'chirishda xato: {e}")


    try:
        foydalanuvchi_tanlovi = int(query.data.split("_")[1])
        oyin = context.user_data['oyat_oyini']
        togri_raqam = oyin.joriy_oyat['surah']['number']
        user_id = query.from_user.id

        if foydalanuvchi_tanlovi == togri_raqam:
            update_user_stats(user_id, correct_answer=True)
            xabar = "✅ To'g'ri! Tabriklaymiz! 🎉"
        else:
            update_user_stats(user_id)
            togri_sura = next(s['name'] for s in SURAH_NAMES if s['number'] == togri_raqam)
            xabar = f"❌ Noto'g'ri! To'g'ri javob: {togri_sura}"

        tugmalar = [
            [InlineKeyboardButton("➡️ Keyingi savol", callback_data="keyingi_savol")],
            [InlineKeyboardButton("📊 Natijalar", callback_data="natijalarni_korsatish")],
            [InlineKeyboardButton("🏠 Bosh menyu", callback_data="bosh_menyu")]
        ]

        try:
            context.bot.delete_message(
                chat_id=chat_id,
                message_id=query.message.message_id
            )
        except Exception as e:
            logger.error(f"Eski xabarni o'chirishda xato: {e}")

        context.bot.send_message(
            chat_id=chat_id,
            text=f"{xabar}\n\nKeyingi savolga o'tish uchun tugmalardan foydalaning:",
            reply_markup=InlineKeyboardMarkup(tugmalar)
        )

    except Exception as e:
        logger.error(f"Javobni tekshirishda xato: {e}")
        context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ Javobingizni tekshirishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
        )


def kanal_tekshirib_keyingi_savol(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    if kanalga_azo_tekshirish(user_id, context):
        asl_keyingi_savol(update, context)
    else:
        tugmalar = [
            [InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="kanalni_tekshirish_keyingi")],
            [InlineKeyboardButton("📢 Kanalga kirish", url=KANAL_LINK)]
        ]

        try:
            query.edit_message_text(
                text=f"⚠️ O'yinni davom ettirish uchun quyidagi kanalga a'zo bo'lishingiz kerak:\n\n"
                     f"{KANAL_LINK}\n\n"
                     "Kanalga a'zo bo'lganingizdan so'ng «✅ A'zo bo'ldim» tugmasini bosing.",
                reply_markup=InlineKeyboardMarkup(tugmalar)
            )
        except Exception as e:
            context.bot.send_message(
                chat_id=user_id,
                text=f"⚠️ O'yinni davom ettirish uchun quyidagi kanalga a'zo bo'lishingiz kerak:\n\n"
                     f"{KANAL_LINK}\n\n"
                     "Kanalga a'zo bo'lganingizdan so'ng «✅ A'zo bo'ldim» tugmasini bosing.",
                reply_markup=InlineKeyboardMarkup(tugmalar)
            )


def asl_keyingi_savol(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if 'oyat_oyini' not in context.user_data or not context.user_data['oyat_oyini'].joriy_oyat:
        query.edit_message_text(
            text="⚠️ Davom ettirish uchun faol o'yin mavjud emas. Iltimos, yangi o'yin boshlang.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎮 Yangi o'yin", callback_data="oyinni_boshlash")],
                [InlineKeyboardButton("🏠 Bosh menyu", callback_data="bosh_menyu")]
            ])
        )
        return

    try:
        oyin = context.user_data['oyat_oyini']
        if oyin.oxirgi_juz:
            query.data = f"juz_{oyin.oxirgi_juz}"
        else:
            query.data = "juz_tasodifiy"

        juz_tanlash(update, context)
    except Exception as e:
        logger.error(f"Xato: {e}")
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⚠️ Keyingi savolni yuklashda xatolik. Iltimos, qayta urinib ko'ring."
        )


def natijalarni_korsatish(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    natijalar = get_user_stats(user_id)
    togri = natijalar['correct_answers']
    urinishlar = natijalar['total_attempts']
    aniqlik = (togri / urinishlar * 100) if urinishlar > 0 else 0

    tugmalar = []

    if 'oyat_oyini' in context.user_data and context.user_data['oyat_oyini'].joriy_oyat:
        tugmalar.append([InlineKeyboardButton("🔄 O'yinni davom ettirish", callback_data="keyingi_savol")])

    tugmalar.extend([
        [InlineKeyboardButton("🎮 Yangi o'yin", callback_data="oyinni_boshlash")],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data="bosh_menyu")],
        [InlineKeyboardButton("🏆 Top 10 o'yinchilar", callback_data="top_10ni_korsatish")],
        [InlineKeyboardButton("📈 Mening reytingim", callback_data="mening_reytingim")],
    ])

    try:
        query.edit_message_text(
            f"📊 Sizning natijalaringiz:\n\n"
            f"✅ To'g'ri javoblar: {togri}\n"
            f"❌ Noto'g'ri javoblar: {urinishlar - togri}\n"
            f"📈 Aniqlik: {aniqlik:.1f}%\n\n"
            f"Quyidagi tugmalardan foydalaning:",
            reply_markup=InlineKeyboardMarkup(tugmalar))
    except Exception as e:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"📊 Sizning natijalaringiz:\n\n"
                 f"✅ To'g'ri javoblar: {togri}\n"
                 f"❌ Noto'g'ri javoblar: {urinishlar - togri}\n"
                 f"📈 Aniqlik: {aniqlik:.1f}%\n\n"
                 f"Quyidagi tugmalardan foydalaning:",
            reply_markup=InlineKeyboardMarkup(tugmalar)
        )

def top_10ni_korsatish(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    eng_yaxshilar = get_top_10_users()

    if not eng_yaxshilar:
        matn = "⚠️ Hali yetarli statistik ma'lumotlar mavjud emas."
    else:
        matn = "🏆 Eng yaxshi 10 o'yinchi:\n\n"
        for i, (ism, foydalanuvchi_nomi, togri, urinishlar, aniqlik) in enumerate(eng_yaxshilar, 1):
            # Maxsus belgilardan tozalash
            nom = f"@{foydalanuvchi_nomi}" if foydalanuvchi_nomi else ism
            matn += f"{i}. {nom} - {togri}/{urinishlar} ({aniqlik:.1f}% aniqlik)\n"

    tugmalar = [[InlineKeyboardButton("🔙 Orqaga", callback_data="mening_natijalarim")]]

    try:
        query.edit_message_text(
            text=matn,
            reply_markup=InlineKeyboardMarkup(tugmalar),
            parse_mode=None  # Formatlashsiz yuborish
        )
    except Exception as e:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=matn,
            reply_markup=InlineKeyboardMarkup(tugmalar),
            parse_mode=None
        )

def mening_reytingim(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    pozitsiya = get_user_position(user_id)

    if not pozitsiya:
        matn = ("📊 Sizning statistikangiz hali yetarli emas.\n"
                "Kamida 5 ta savolga javob berishingiz kerak.")
    else:
        joriy = pozitsiya['current_user']
        yaqin = pozitsiya['nearby_users']
        jami = pozitsiya['total_players']

        matn = (f"📈 Sizning reytingingiz: {joriy[5]}/{jami}\n\n"
                f"✅ To'g'ri javoblar: {joriy[2]}\n"
                f"❌ Noto'g'ri javoblar: {joriy[3] - joriy[2]}\n"
                f"📊 Aniqlik: {joriy[4]:.1f}%\n\n"
                "Yaqin atrofdagi o'yinchilar:\n")

        for foydalanuvchi in yaqin:
            prefiks = "👉 " if foydalanuvchi[0] == user_id else "● "
            matn += f"{prefiks}{foydalanuvchi[1]} - {foydalanuvchi[4]:.1f}%\n"

    # Orqaga qaytish tugmasi
    tugmalar = [[InlineKeyboardButton("🔙 Orqaga", callback_data="mening_natijalarim")]]

    try:
        query.edit_message_text(
            text=matn,
            reply_markup=InlineKeyboardMarkup(tugmalar)
        )
    except Exception as e:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=matn,
            reply_markup=InlineKeyboardMarkup(tugmalar)
        )


def kanalni_tekshirish(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    if kanalga_azo_tekshirish(user_id, context):
        asl_oynani_boshlash(update, context)
    else:
        try:
            query.edit_message_text(
                text="⚠️ Siz hali kanalga a'zo bo'lmadingiz. Iltimos, quyidagi kanalga a'zo bo'ling:\n\n"
                     f"{KANAL_LINK}\n\n"
                     "A'zo bo'lganingizdan so'ng ushbu tugmani bosing.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="kanalni_tekshirish")],
                    [InlineKeyboardButton("📢 Kanalga kirish", url=KANAL_LINK)]
                ]))
        except Exception as e:
            context.bot.send_message(
                chat_id=user_id,
                text="⚠️ Siz hali kanalga a'zo bo'lmadingiz. Iltimos, quyidagi kanalga a'zo bo'ling:\n\n"
                     f"{KANAL_LINK}\n\n"
                     "A'zo bo'lganingizdan so'ng ushbu tugmani bosing.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="kanalni_tekshirish")],
                    [InlineKeyboardButton("📢 Kanalga kirish", url=KANAL_LINK)]
                ])
            )


def kanalni_tekshirish_keyingi(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    if kanalga_azo_tekshirish(user_id, context):
        asl_keyingi_savol(update, context)
    else:
        try:
            query.edit_message_text(
                text="⚠️ Siz hali kanalga a'zo bo'lmadingiz. Iltimos, quyidagi kanalga a'zo bo'ling:\n\n"
                     f"{KANAL_LINK}\n\n"
                     "A'zo bo'lganingizdan so'ng ushbu tugmani bosing.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="kanalni_tekshirish_keyingi")],
                    [InlineKeyboardButton("📢 Kanalga kirish", url=KANAL_LINK)]
                ])
            )
        except Exception as e:
            context.bot.send_message(
                chat_id=user_id,
                text="⚠️ Siz hali kanalga a'zo bo'lmadingiz. Iltimos, quyidagi kanalga a'zo bo'ling:\n\n"
                     f"{KANAL_LINK}\n\n"
                     "A'zo bo'lganingizdan so'ng ushbu tugmani bosing.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ A'zo bo'ldim", callback_data="kanalni_tekshirish_keyingi")],
                    [InlineKeyboardButton("📢 Kanalga kirish", url=KANAL_LINK)]
                ])
            )


def bosh_menyuga_qaytish(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    chat_id = query.message.chat_id

    user = query.from_user
    logger.info(f"Foydalanuvchi {user.first_name} bosh menyuga qaytdi")

    # Delete any lingering audio when returning to main menu
    oyat_oyini_instance = context.user_data.get('oyat_oyini')
    if oyat_oyini_instance and oyat_oyini_instance.last_audio_message_id:
        try:
            context.bot.delete_message(
                chat_id=chat_id,
                message_id=oyat_oyini_instance.last_audio_message_id
            )
            oyat_oyini_instance.last_audio_message_id = None
        except Exception as e:
            logger.warning(f"Bosh menyuga qaytishda audio xabarini o'chirishda xato: {e}")

    try:
        try:
            query.edit_message_text(
                text="🏠 Bosh menyu, bo'limlardan birini tanlang:",
                reply_markup=main_buttons()
            )
        except Exception as edit_error:
            logger.warning(f"Xabarni o'zgartirib bo'lmadi, yangi xabar yuboriladi: {edit_error}")

            context.bot.send_message(
                chat_id=chat_id,
                text="🏠 Bosh menyu, bo'limlardan birini tanlang:",
                reply_markup=main_buttons()
            )

            try:
                context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=query.message.message_id
                )
            except Exception as delete_error:
                logger.warning(f"Eski xabarni o'chirib bo'lmadi: {delete_error}")

    except Exception as e:
        logger.error(f"Bosh menyuga qaytishda xato: {e}")
        context.bot.send_message(
            chat_id=chat_id,
            text="🏠 Bosh menyu, bo'limlardan birini tanlang:",
            reply_markup=main_buttons()
        )


def setup_handlers(dispatcher):
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^Oyatlarni toping 🔍$'), oyat_topish))
    dispatcher.add_handler(CallbackQueryHandler(oyat_topish, pattern='^oyat_topish$'))
    dispatcher.add_handler(CallbackQueryHandler(kanal_tekshirib_oynash, pattern='^oyinni_boshlash$'))
    dispatcher.add_handler(CallbackQueryHandler(bosh_menyuga_qaytish, pattern='^bosh_menyu$'))
    dispatcher.add_handler(CallbackQueryHandler(juz_tanlash, pattern='^juz_'))
    dispatcher.add_handler(CallbackQueryHandler(javobni_tekshirish, pattern='^javob_'))
    dispatcher.add_handler(CallbackQueryHandler(kanal_tekshirib_keyingi_savol, pattern='^keyingi_savol$'))
    dispatcher.add_handler(CallbackQueryHandler(natijalarni_korsatish, pattern='^natijalarni_korsatish$'))
    dispatcher.add_handler(CallbackQueryHandler(natijalarni_korsatish, pattern='^mening_natijalarim$'))
    dispatcher.add_handler(CallbackQueryHandler(kanalni_tekshirish, pattern='^kanalni_tekshirish$'))
    dispatcher.add_handler(CallbackQueryHandler(kanalni_tekshirish_keyingi, pattern='^kanalni_tekshirish_keyingi$'))
    dispatcher.add_handler(CallbackQueryHandler(top_10ni_korsatish, pattern='^top_10ni_korsatish$'))
    dispatcher.add_handler(CallbackQueryHandler(mening_reytingim, pattern='^mening_reytingim$'))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))