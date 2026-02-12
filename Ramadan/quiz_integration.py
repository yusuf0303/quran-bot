from telegram import Update, Poll, ParseMode, PollAnswer, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from Ramadan.database import add_points, DB_PATH
from Suralarni_toping.surahs import SURAH_NAMES
from Suralarni_toping.database import DB_PATH as QURAN_DB_PATH
import time
import json
import sqlite3
import random
import os
import requests
import io

def generate_friday_quiz_questions():
    # Load translation (root directory)
    json_path = "quran_trans_uz.json"
    if not os.path.exists(json_path):
        json_path = os.path.join("Suralarni_toping", "quran_trans_uz.json")
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Flatten all ayahs into a list
    all_ayahs = []
    surahs = data['data']['surahs']
    for surah in surahs:
        surah_id = surah['number']
        
        for ayah in surah['ayahs']:
            all_ayahs.append({
                'surah_id': surah_id,
                'ayah_id': ayah['numberInSurah'],
                'global_id': ayah['number'],
                'content': ayah['text'], 
            })
            
    # Select 20 random ayahs
    selected_ayahs = random.sample(all_ayahs, 20)
    
    questions = []
    
    # Create mapping from SURAH_NAMES list
    surah_map = {s['number']: s['name'] for s in SURAH_NAMES}
    all_surah_names = list(surah_map.values())

    for ayah in selected_ayahs:
        surah_id = ayah['surah_id']
        surah_name = surah_map.get(surah_id, "Noma'lum")
        
        # Correct answer with Ayah number
        correct_option = f"{surah_name} {ayah['ayah_id']}-oyat"
        
        # Distractors
        # We need to generate distractors that also look like "Surah X Ayah Y"
        # Logic: Pick random surahs from map, and random ayah numbers
        options = [correct_option]
        while len(options) < 4:
            rand_s_id = random.choice(list(surah_map.keys()))
            rand_s_name = surah_map[rand_s_id]
            # Random ayah number between 1 and 200 (simple approximation)
            rand_a_num = random.randint(1, 100)
            
            opt = f"{rand_s_name} {rand_a_num}-oyat"
            if opt not in options:
                options.append(opt)
        
        random.shuffle(options)
        correct_idx = options.index(correct_option)
        
        questions.append({
            'surah_id': surah_id,
            'ayah_id': ayah['ayah_id'],
            'global_id': ayah['global_id'],
            'content': ayah['content'],
            'options': options,
            'correct_index': correct_idx
        })
    
    return questions

from datetime import datetime
import logging
logger = logging.getLogger(__name__)

def send_friday_quiz_notification(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id if update else context.job.context
    
    keyboard = [[InlineKeyboardButton("Testni boshlash 🚀", callback_data="start_friday_test")]]
    text = (
        "🌟 **Juma Testi boshlanmoqda!**\n\n"
        "Bugun juma! Haftalik testni ishlab ko'proq ball ishlab oling.\n"
        "Testni o'zingizga qulay vaqtda, **23:59 gacha** boshlashingiz mumkin.\n\n"
        "Imkoniyatni qo'ldan boy bermang! 🚀"
    )
    context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def handle_friday_test_start(update: Update, context: CallbackContext):
    try:
        query = update.callback_query
            
        logger.info(f"handle_friday_test_start triggered by user {update.effective_user.id}")

        import pytz
        tashkent_tz = pytz.timezone('Asia/Tashkent')
        now = datetime.now(tashkent_tz)
        # Debugging: Allow Friday (4)    
        if now.weekday() not in [4]:
             logger.info("Not Friday, showing alert.")
             if query:
                query.answer("⚠️ Test vaqti tugagan! Juma kuni qayta kirib urinib ko'ring.", show_alert=True)
             else:
                update.message.reply_text("⚠️ Test faqat Juma kunlari bo'ladi.")
             return 

        user_id = update.effective_user.id
        
        # Register session in user_data
        questions = generate_friday_quiz_questions()
        context.user_data['friday_quiz'] = {
            'questions': questions,
            'current_idx': 0,
            'score': 0,
            'start_time': time.time(),
            'time_limit': 60, # 1 minute per question
            'active_job': None,
            'chat_id': update.effective_chat.id, # Store chat ID for poll handling
            'full_name': update.effective_user.full_name # Store name for auto-finish
        }
        
        msg_text = "🌟 **Juma Testi boshlanmoqda!**\nSizga 20 ta oyat (audio va rasm) beriladi. Har bir to'g'ri javob uchun 5 ball!\nHar bir savolga 1 daqiqa vaqt! Omad! 🚀"
        if query:
            query.answer()
            query.edit_message_text(msg_text, parse_mode=ParseMode.MARKDOWN)
        else:
            update.message.reply_text(msg_text, parse_mode=ParseMode.MARKDOWN)
            
        send_friday_question(update, context)
    except Exception as e:
        logger.error(f"Error in handle_friday_test_start: {e}")
        if update.callback_query:
            update.callback_query.answer("Xatolik yuz berdi!", show_alert=True)

def send_friday_question(update: Update, context: CallbackContext, explicit_user_data=None):
    try:
        # Use explicit_user_data if provided (for jobs), otherwise context.user_data
        quiz_data = None
        if explicit_user_data is not None:
            quiz_data = explicit_user_data.get('friday_quiz')
        else:
            quiz_data = context.user_data.get('friday_quiz')
            
        if not quiz_data: return
        
        idx = quiz_data['current_idx']
        if idx >= len(quiz_data['questions']):
            finish_friday_quiz(update, context, explicit_user_data)
            return
        
        q = quiz_data['questions'][idx]
        
        # Robust Chat ID Retrieval
        chat_id = None
        # update might be MockUpdate, need to be careful
        if hasattr(update, 'effective_chat') and update.effective_chat:
            chat_id = update.effective_chat.id
        elif context.job and context.job.context:
             # Job context might be dict or int
             ctx = context.job.context
             if isinstance(ctx, dict): chat_id = ctx.get('chat_id')
             else: chat_id = ctx
        
        # If still no chat_id (e.g. from poll_answer), try user id as chat id for private chats
        if not chat_id and hasattr(update, 'poll_answer') and update.poll_answer:
            chat_id = update.poll_answer.user.id
            
        if not chat_id:
            logger.error("Could not determine chat_id in send_friday_question")
            return

        # Send Audio
        audio_url = f"https://cdn.islamic.network/quran/audio/128/ar.alafasy/{q['global_id']}.mp3"
        try:
            # Download audio to memory to strip metadata/custom title
            response = requests.get(audio_url)
            if response.status_code == 200:
                audio_file = io.BytesIO(response.content)
                audio_file.name = "savol.mp3" # Generic name
                context.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio_file,
                    title="Juma Testi",
                    performer="KalomUz Bot",
                    protect_content=True
                )
            else:
                layout_msg = context.bot.send_message(chat_id, "⚠️ Audio yuklanmadi.")
        except Exception as e:
            logger.error(f"Failed to send audio: {e}")
            context.bot.send_message(chat_id, "⚠️ Audio yuklashda xatolik bo'ldi.")

        # Send Image
        image_url = f"https://cdn.islamic.network/quran/images/high-resolution/{q['surah_id']}_{q['ayah_id']}.png"
        try:
            context.bot.send_photo(
                chat_id=chat_id,
                photo=image_url,
                caption=f"📜 **{idx+1}-savol**",
                protect_content=True
            )
        except Exception as e:
            logger.error(f"Failed to send image: {e}")
            context.bot.send_message(chat_id, "⚠️ Rasm yuklashda xatolik bo'ldi.")

        # Send Poll
        msg = context.bot.send_poll(
            chat_id=chat_id,
            question=f"Bu oyat qaysi suraga tegishli? ({idx+1}/20)",
            options=q['options'],
            type=Poll.QUIZ,
            correct_option_id=q['correct_index'],
            is_anonymous=False,
            explanation=f"To'g'ri javob: {q['options'][q['correct_index']]}",
            open_period=60, # 60 seconds
            protect_content=True # Anti-cheat: disable forwarding
        )
        
        if explicit_user_data is not None:
             explicit_user_data['last_friday_poll'] = msg.poll.id
        else:
             context.user_data['last_friday_poll'] = msg.poll.id
        
        # Auto-next job for Friday quiz (Timer-based progression + 1s buffer)
        # Check effective_user again
        user_id = None
        if hasattr(update, 'effective_user') and update.effective_user:
             user_id = update.effective_user.id
        elif hasattr(update, 'poll_answer') and update.poll_answer:
             user_id = update.poll_answer.user.id
             
        if user_id: 
            # Cancel previous job
            if quiz_data.get('active_job'):
                try:
                    quiz_data['active_job'].schedule_removal()
                except Exception:
                    pass # Job might already be removed/finished

            quiz_data['active_job'] = context.job_queue.run_once(
                job_friday_auto_next,
                when=65, # 60s poll + 5s buffer
                context={'chat_id': chat_id, 'user_id': user_id, 'idx': idx}
            )
    except Exception as e:
        logger.error(f"Error in send_friday_question: {e}")

def job_friday_auto_next(context: CallbackContext):
    job_data = context.job.context
    chat_id, user_id, trigger_idx = job_data['chat_id'], job_data['user_id'], job_data['idx']
    
    # Manually retrieve user_data since this is a job context
    user_data = context.dispatcher.user_data.get(user_id)
    quiz = user_data.get('friday_quiz') if user_data else None
    
    if quiz and quiz['current_idx'] == trigger_idx:
        quiz['current_idx'] += 1
        
        full_name = quiz.get('full_name', 'Foydalanuvchi')
        
        class MockUpdate:
            def __init__(self, cid, uid, fname):
                self.effective_chat = type('obj', (object,), {'id': cid, 'type': 'group'})()
                self.effective_user = type('obj', (object,), {'id': uid, 'full_name': fname})()
                self.poll_answer = None # Add this to avoid attribute errors
        
        # Pass user_data proactively
        send_friday_question(MockUpdate(chat_id, user_id, full_name), context, explicit_user_data=user_data)
    
from datetime import datetime

from datetime import datetime

def finish_friday_quiz(update: Update, context: CallbackContext, explicit_user_data=None):
    # Determine which user_data to use
    user_data = explicit_user_data if explicit_user_data is not None else context.user_data
    quiz_data = user_data.get('friday_quiz')
    
    if not quiz_data: return
    
    score = quiz_data['score']
    points = score * 5
    
    # Calculate time
    total_seconds = int(time.time() - quiz_data['start_time'])
    mins, secs = divmod(total_seconds, 60)
    time_str = f"{mins:02d}:{secs:02d}"
    
    user_id = update.effective_user.id
    
    # Anti-cheat: Friday quiz ID based on date
    friday_id = f"friday_{datetime.now().strftime('%Y_%m_%d')}"
    
    from Ramadan.database import add_points, is_quiz_rewarded, record_quiz_reward, register_contest_user
    
    contest_note = ""
    from Ramadan.contest_logic import escape_markdown
    safe_name = escape_markdown(update.effective_user.full_name)

    if is_quiz_rewarded(user_id, friday_id):
        contest_note = "\n\n⚠️ *Eslatma: Bu haftalik juma testidan avval ball olgansiz. Qayta ishlash ball qo'shmaydi, lekin ilm olish uchun foydali!* 📚"
    else:
        register_contest_user(user_id, update.effective_user.full_name) # Store original name in DB
        add_points(user_id, points)
        record_quiz_reward(user_id, friday_id, score, quiz_type='friday')
        contest_note = f"\n\n💰 **Konkurs uchun: +{points} ball!**"
    
    try:
        update.message.reply_text(
            f"🏁 **Juma Testi yakunlandi!**\n\n"
            f"👤 {safe_name}\n"
            f"✅ To'g'ri javoblar: {score}/20\n"
            f"⏳ Ketgan vaqt: {time_str}"
            f"{contest_note}\n\n"
            "Barakalloh! Bilimingiz ziyoda bo'lsin. 🎊",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        # Fallback if reply_text fails (e.g. not a message update)
        logger.error(f"Error in finish_friday_quiz reply_text: {e}. Trying fallback.")
        try:
            chat_id = update.effective_chat.id
            context.bot.send_message(
                chat_id=chat_id,
                text=f"🏁 **Juma Testi yakunlandi!**\n\n"
                f"👤 {safe_name}\n"
                f"✅ To'g'ri javoblar: {score}/20\n"
                f"⏳ Ketgan vaqt: {time_str}"
                f"{contest_note}\n\n"
                "Barakalloh! Bilimingiz ziyoda bo'lsin. 🎊",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e2:
            logger.error(f"Critical error sending finish_friday_quiz fallback: {e2}")

    user_data['friday_quiz'] = None
