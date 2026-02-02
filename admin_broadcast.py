from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from Suralarni_toping.database import get_all_user_ids
from Suralar.menu_button import main_buttons
import os
import time
import logging

logger = logging.getLogger(__name__)

# States
ASK_MESSAGE = 0
WAIT_FOR_ACTION = 1
ASK_BTN_TEXT = 2
ASK_BTN_URL = 3

def get_admin_id():
    return int(os.getenv("ADMIN_ID", 0))

def start_broadcast(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != get_admin_id():
        return ConversationHandler.END
    
    # Cleanup context
    context.user_data.pop('broadcast_message', None)
    context.user_data.pop('broadcast_buttons', None)
    context.user_data.pop('preview_msg_id', None)
    
    update.message.reply_text(
        "📢 Xabar yuborish rejimidasiz.\n\n"
        "Xabar matnini (yoki rasm/video) yuboring:",
        reply_markup=ReplyKeyboardMarkup([['Bekor qilish ❌']], resize_keyboard=True, one_time_keyboard=True)
    )
    return ASK_MESSAGE

def receive_message(update: Update, context: CallbackContext):
    msg = update.message
    if msg.text == "Bekor qilish ❌":
        return cancel_broadcast(update, context)
    
    context.user_data['broadcast_message'] = msg
    context.user_data['broadcast_buttons'] = [] # List of lists
    
    # Initial Preview with "Add Button"
    initial_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Tugma qo'shish ➕", callback_data="add_first")],
        [InlineKeyboardButton("Yuborish 🚀", callback_data="broadcast_finish"), 
         InlineKeyboardButton("Bekor qilish ❌", callback_data="broadcast_cancel")]
    ])
    
    update.message.reply_text("📨 Xabar preview (tahrirlash rejimi):", reply_markup=ReplyKeyboardRemove())
    
    try:
        preview_msg = msg.copy(chat_id=update.effective_chat.id, reply_markup=initial_markup)
        context.user_data['preview_msg_id'] = preview_msg.message_id
    except Exception as e:
        update.message.reply_text(f"Xatolik: {e}")
        return ConversationHandler.END
        
    return WAIT_FOR_ACTION

def generate_builder_markup(buttons):
    # Deep copy to avoid modifying actual data
    display_rows = [row[:] for row in buttons]
    
    # Add "Side" button to the last row if exists
    if display_rows:
        display_rows[-1].append(InlineKeyboardButton("➕", callback_data="add_side"))
    else:
        # Should not happen via this function usually, but fallback
        pass
        
    # Add "Down" button in new row
    display_rows.append([InlineKeyboardButton("Pastidan ⬇️", callback_data="add_down")])
    
    # Footer
    display_rows.append([
        InlineKeyboardButton("Tugatish ✅", callback_data="broadcast_finish"),
        InlineKeyboardButton("Bekor qilish ❌", callback_data="broadcast_cancel")
    ])
    
    return InlineKeyboardMarkup(display_rows)

def add_msg_to_delete(context, msg_id):
    if 'delete_msg_ids' not in context.user_data:
        context.user_data['delete_msg_ids'] = []
    context.user_data['delete_msg_ids'].append(msg_id)

def cleanup_messages(context, chat_id):
    if 'delete_msg_ids' in context.user_data:
        for mid in context.user_data['delete_msg_ids']:
            try:
                context.bot.delete_message(chat_id=chat_id, message_id=mid)
            except:
                pass
        context.user_data['delete_msg_ids'] = []

def handle_builder_action(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        query.answer()
    except:
        pass
    
    data = query.data
    
    try:
        if data == "broadcast_cancel":
            try:
                query.edit_message_reply_markup(None)
            except:
                pass
            query.message.reply_text("Bekor qilindi.", reply_markup=main_buttons(get_admin_id()))
            return ConversationHandler.END
            
        if data == "broadcast_finish":
            # Finalize
            buttons = context.user_data.get('broadcast_buttons', [])
            final_markup = InlineKeyboardMarkup(buttons) if buttons else None
            
            # Update preview to remove controls
            try:
                query.edit_message_reply_markup(final_markup)
            except:
                pass
                
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Tasdiqlaysizmi?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Ha, yuborish 🚀", callback_data="confirm_send")],
                    [InlineKeyboardButton("Yo'q ❌", callback_data="broadcast_cancel")]
                ])
            )
            return WAIT_FOR_ACTION 
        
        if data == "confirm_send":
            return execute_broadcast(update, context)
            
        # Adding buttons
        if data == "add_first":
            context.user_data['add_mode'] = 'new_row'
        elif data == "add_down":
            context.user_data['add_mode'] = 'new_row'
        elif data == "add_side":
            context.user_data['add_mode'] = 'side'
            
        m = query.message.reply_text("Tugma matnini yozing:", reply_markup=ReplyKeyboardMarkup([['Bekor qilish ❌']], resize_keyboard=True))
        add_msg_to_delete(context, m.message_id) # Track prompt
        return ASK_BTN_TEXT
        
    except Exception as e:
        logger.error(f"Error in handle_builder_action: {e}")
        try:
            query.message.reply_text("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        except:
            pass
        return ConversationHandler.END

def get_btn_text(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "Bekor qilish ❌":
        return cancel_broadcast(update, context)
        
    add_msg_to_delete(context, update.message.message_id) # Track user answer
    context.user_data['temp_btn_text'] = text
    
    m = update.message.reply_text("Endi linkni (URL) yozing:")
    add_msg_to_delete(context, m.message_id) # Track next prompt
    return ASK_BTN_URL

def get_btn_url(update: Update, context: CallbackContext):
    url = update.message.text
    if url == "Bekor qilish ❌":
        return cancel_broadcast(update, context)
        
    add_msg_to_delete(context, update.message.message_id) # Track user answer
    
    # Validate URL simple check
    if not url.startswith("http"):
        m = update.message.reply_text("Iltimos, to'g'ri URL kiriting (http/https bilan).")
        add_msg_to_delete(context, m.message_id)
        return ASK_BTN_URL
        
    # Add button
    try:
        btn = InlineKeyboardButton(context.user_data['temp_btn_text'], url=url)
        buttons = context.user_data.get('broadcast_buttons', [])
        mode = context.user_data.get('add_mode', 'new_row')
        
        if mode == 'new_row' or not buttons:
            buttons.append([btn])
        else:
            # Add side
            buttons[-1].append(btn)
            
        context.user_data['broadcast_buttons'] = buttons
        
        # Update Preview
        markup = generate_builder_markup(buttons)
        preview_id = context.user_data.get('preview_msg_id')
        
        try:
            context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=preview_id,
                reply_markup=markup
            )
            # Cleanup all intermediate messages
            cleanup_messages(context, update.effective_chat.id)
            
            # Send confirmation and delete it immediately/soon or just don't send? 
            # User request: "Bu xabarlar o'chirib yuborilsin tugma qo'shilganda"
            # referring to the "Tugma qo'shildi" message as well.
            # I will assume we don't need to send it if we just cleaned up. 
            # But feedback is good. Let's send a temp message that autodeletes? 
            # Or just rely on the preview update as visual feedback.
            # The preview update IS the feedback.
            # Let's send a quick toast message then delete it? 
            # Actually, "reply_markup=ReplyKeyboardRemove()" was in the original confirmation.
            # We need to remove the "Bekor qilish" keyboard from the user's view.
            
            m_conf = update.message.reply_text("✅", reply_markup=ReplyKeyboardRemove())
            # Immediately delete the "tick" message too?
            try:
                context.bot.delete_message(chat_id=update.effective_chat.id, message_id=m_conf.message_id)
            except: pass
            
        except Exception as e:
            update.message.reply_text(f"Preview yangilashda xato: {e}")
            
    except Exception as e:
         logger.error(f"Error adding button: {e}")
         update.message.reply_text("Tugma qo'shishda xatolik!")
         return ConversationHandler.END
        
    return WAIT_FOR_ACTION

def execute_broadcast(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        query.answer()
    except:
        pass
    
    try:
        query.edit_message_text("Xabar yuborish boshlandi... 🚀")
        
        users = get_all_user_ids()
        message = context.user_data.get('broadcast_message')
        buttons = context.user_data.get('broadcast_buttons', [])
        markup = InlineKeyboardMarkup(buttons) if buttons else None
        
        success = 0
        blocked = 0
        start = time.time()
        
        status_msg = context.bot.send_message(chat_id=update.effective_chat.id, text="Yuborilmoqda...")
        
        for i, uid in enumerate(users):
            try:
                message.copy(chat_id=uid, reply_markup=markup)
                success += 1
            except:
                blocked += 1
            
            if i % 20 == 0:
                try:
                    context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=status_msg.message_id,
                        text=f"Jarayon: {i}/{len(users)}\n✅ {success}\n🚫 {blocked}"
                    )
                except: pass
            time.sleep(0.05)
            
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Tugatildi!\n✅ {success}\n🚫 {blocked}\n⏱ {round(time.time()-start, 2)}s",
            reply_markup=main_buttons(get_admin_id())
        )
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        try:
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Xatolik: {e}")
        except: pass
        
    return ConversationHandler.END

def cancel_broadcast(update: Update, context: CallbackContext):
    update.message.reply_text("Bekor qilindi.", reply_markup=main_buttons(get_admin_id()))
    return ConversationHandler.END

def setup_admin_handlers(dp):
    conv = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex("^Xabar yuborish 📤$"), start_broadcast)],
        states={
            ASK_MESSAGE: [MessageHandler(Filters.all & ~Filters.command, receive_message)],
            WAIT_FOR_ACTION: [CallbackQueryHandler(handle_builder_action)],
            ASK_BTN_TEXT: [MessageHandler(Filters.text, get_btn_text)],
            ASK_BTN_URL: [MessageHandler(Filters.text, get_btn_url)],
        },
        fallbacks=[CommandHandler('cancel', cancel_broadcast), MessageHandler(Filters.regex("^Bekor qilish ❌$"), cancel_broadcast)]
    )
    dp.add_handler(conv)

