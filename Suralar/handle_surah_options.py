
from Suralar.menu_button import logger

from Suralar.show_ayah_text import show_ayah_text
from Suralar.show_translation import show_translation, show_ayah_list


def handle_surah_options(query, context):
    """Sura bo'yicha tanlovlarga to'liq javob berish funksiyasi"""
    try:
        query.answer("Amal bajarilmoqda...")  # Foydalanuvchiga bildirishnoma

        option = query.data
        user_data = context.user_data
        surah_num = user_data.get('surah_pages_sec')

        # Sura tanlanmaganligini tekshirish
        if not surah_num:
            query.answer("❗️ Avval surani tanlang.", show_alert=True)
            return

        # Matn ko'rsatish
        if option == 'show_text':
            user_data.update({
                'current_ayah': 1,
                'translation_ayah': 1,
                'ayah_page': 0  # Sahifalash uchun
            })
            show_ayah_text(query, context)

        # Tarjima ko'rsatish
        elif option == 'show_translation':
            if 'current_ayah' not in user_data:
                user_data['current_ayah'] = 1
            user_data['translation_ayah'] = user_data['current_ayah']
            show_translation(query, context)

        # Oyatlar ro'yxatini ko'rsatish
        elif option == 'list_ayahs':
            user_data.update({
                'ayah_page': 0,  # Sahifa raqami
                'last_btn': 0,  # Oxirgi ko'rsatilgan tugma
                'current_ayah': 1,  # Boshlang'ich oyat
                'current_surah': surah_num  # Joriy sura
            })
            show_ayah_list(query, context)

        else:
            query.answer("⚠️ Bunday buyruq mavjud emas", show_alert=True)

    except Exception as e:
        logger.error(f"Sura tanlovida xato [Option: {option}]: {str(e)}", exc_info=True)

        try:
            # Xabarni yangilashga urinish
            query.edit_message_text("⚠️ Amalni bajarishda xatolik. Qayta urunib ko'ring.")
        except:
            # Yangilab bo'lmasa, yangi xabar yuborish
            context.bot.send_message(
                chat_id=query.from_user.id,
                text="⚠️ Xatolik yuz berdi. Iltimos, qayta urunib ko'ring."
            )