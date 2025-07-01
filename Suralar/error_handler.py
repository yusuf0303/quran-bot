from Suralar.menu_button import logger


def error_handler(update, context):

    logger.error(msg="Exception occurred:", exc_info=context.error)

    try:
        if update.callback_query:
            if update.callback_query.message:
                update.callback_query.edit_message_text(
                    "⚠️ Botda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
                )
            else:
                context.bot.send_message(
                    chat_id=update.callback_query.from_user.id,
                    text="⚠️ Botda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
                )
        elif update.message:
            update.message.reply_text("⚠️ Botda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")
    except Exception as e:
        logger.error(f"Error handler itself failed: {e}")

