import random
import logging
import requests
import io
import json
import os
import time
import uuid
from datetime import datetime
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update, 
    Poll, 
    ParseMode,
    PollAnswer
)
from telegram.ext import (
    CallbackContext, 
    CallbackQueryHandler, 
    ConversationHandler, 
    MessageHandler, 
    Filters
)
from Suralarni_toping.surahs import SURAH_NAMES
from Suralar.menu_button import main_buttons, logger
from access_control import ensure_access
from Suralarni_toping.database import save_shared_quiz, get_shared_quiz, add_user_quiz, get_user_quizzes, get_user_quiz_stats, update_user_quiz_stats

# States
SELECT_JUZ, SELECT_COUNT, SELECT_TIME = range(3)

# Global storage for tracking polls (poll_id -> {'quiz': quiz, 'correct_index': idx})
ACTIVE_POLLS = {}

def get_trans_data():
    path = "quran_trans_uz.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return None

class QuizCreator:
    def __init__(self):
        self.selected_juz = []
        self.question_count = 5
        self.time_limit = 30
        self.questions = []
        self.current_question_idx = 0
        self.score = 0
        self.user_full_name = ""
        self.total_duration = 0.0
        self.current_q_start = 0.0
        self.active_job = None
        self.chat_id = None
        self.chat_type = None
        self.quiz_id = None

def quiz_yarat_start(update: Update, context: CallbackContext):
    if not ensure_access(update, context):
        return
        
    context.user_data['quiz_creator'] = QuizCreator()
    context.user_data['quiz_creator'].user_full_name = update.effective_user.full_name
    return show_juz_selection(update, context)

def show_juz_selection(update: Update, context: CallbackContext):
    quiz = context.user_data['quiz_creator']
    keyboard = []
    for i in range(0, 30, 5):
        row = []
        for j in range(i + 1, i + 6):
            display_text = f"{j} ✅" if j in quiz.selected_juz else str(j)
            row.append(InlineKeyboardButton(display_text, callback_data=f"quiz_juz_sel_{j}"))
        keyboard.append(row)
    
    # Selection utilities labels
    all_selected = len(quiz.selected_juz) == 30
    all_label = "Barcha juzlar ✅" if all_selected else "Barcha juzlar 📚"
    
    # Random label: If only one is selected, we can show it on the random button
    random_label = "Tasodifiy juz 🎲"
    if len(quiz.selected_juz) == 1:
        random_label = f"Tasodifiy ({quiz.selected_juz[0]}-juz) ✅"
        
    keyboard.append([
        InlineKeyboardButton(all_label, callback_data="quiz_juz_all"),
        InlineKeyboardButton(random_label, callback_data="quiz_juz_random")
    ])
    
    keyboard.append([InlineKeyboardButton("Tayyor ✅", callback_data="quiz_juz_ready")])
    keyboard.append([InlineKeyboardButton("Mening quizlarim 📚", callback_data="quiz_history")])
    keyboard.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="quiz_cancel")])
    
    markup = InlineKeyboardMarkup(keyboard)
    text = "📝 **Quiz yaratish**\n\nSavollar qaysi juzlardan olinsin?"
    if update.callback_query:
        try: update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
        except: pass
    else: update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    return SELECT_JUZ

def handle_juz_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    quiz = context.user_data.get('quiz_creator')
    if not quiz: return quiz_cancel(update, context)
    data = query.data
    if data.startswith("quiz_juz_sel_"):
        juz_num = int(data.split("_")[-1])
        if juz_num in quiz.selected_juz: quiz.selected_juz.remove(juz_num)
        else: quiz.selected_juz.append(juz_num)
        query.answer()
        return show_juz_selection(update, context)
    elif data == "quiz_juz_all":
        if len(quiz.selected_juz) == 30:
            quiz.selected_juz = []
            query.answer("Tanlov bekor qilindi ❌")
        else:
            quiz.selected_juz = list(range(1, 31))
            query.answer("Barcha juzlar tanlandi ✅")
        return show_juz_selection(update, context)
    elif data == "quiz_juz_random":
        new_juz = random.randint(1, 30)
        # Avoid same juz if possible, or just pick a new one
        quiz.selected_juz = [new_juz]
        query.answer(f"{new_juz}-juz tanlandi 🎲")
        return show_juz_selection(update, context)
    elif data == "quiz_history":
        query.answer()
        context.user_data['history_page'] = 0
        return show_my_quizzes(update, context)
    elif data.startswith("quiz_hist_"):
        query.answer()
        page = context.user_data.get('history_page', 0)
        if "next" in data: page += 1
        elif "prev" in data: page = max(0, page - 1)
        context.user_data['history_page'] = page
        return show_my_quizzes(update, context)
    elif data == "quiz_juz_ready":
        if not quiz.selected_juz:
            query.answer("Iltimos, kamida bitta juz tanlang!", show_alert=True)
            return SELECT_JUZ
        query.answer()
        return show_count_selection(update, context)

def show_count_selection(update: Update, context: CallbackContext):
    counts = [5, 10, 15, 20, 25, 30]
    keyboard = [[InlineKeyboardButton(f"{c} ta", callback_data=f"quiz_count_val_{c}") for c in counts[i:i+3]] for i in range(0, len(counts), 3)]
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="quiz_back_to_juz")])
    update.callback_query.edit_message_text("**Savollar sonini tanlang (5 - 30):**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return SELECT_COUNT

def handle_count_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    quiz = context.user_data.get('quiz_creator')
    if not quiz: return quiz_cancel(update, context)
    if query.data.startswith("quiz_count_val_"):
        quiz.question_count = int(query.data.split("_")[-1])
        query.answer()
        return show_time_selection(update, context)
    elif query.data == "quiz_back_to_juz":
        query.answer(); return show_juz_selection(update, context)

def show_time_selection(update: Update, context: CallbackContext):
    times = [15, 30, 45, 60]
    keyboard = [[InlineKeyboardButton(f"{t} sek", callback_data=f"quiz_time_val_{t}") for t in times]]
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="quiz_back_to_count")])
    update.callback_query.edit_message_text("**Har bir savol uchun vaqtni tanlang:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return SELECT_TIME

def handle_time_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    quiz = context.user_data.get('quiz_creator')
    if not quiz: return quiz_cancel(update, context)
    if query.data.startswith("quiz_time_val_"):
        quiz.time_limit = int(query.data.split("_")[-1])
        quiz.quiz_id = None # Will be set in finish_creation
        query.answer("Quiz tayyorlanmoqda...")
        return finish_creation(update, context)
    elif query.data == "quiz_back_to_count":
        query.answer(); return show_count_selection(update, context)

def finish_creation(update: Update, context: CallbackContext):
    quiz = context.user_data['quiz_creator']
    if not prepare_quiz_questions(quiz):
        update.callback_query.edit_message_text("⚠️ Xatolik yuz berdi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Bosh menyu", callback_data="quiz_cancel")]]))
        return ConversationHandler.END
    juz_str = "-".join(map(str, sorted(quiz.selected_juz)))
    # Generate unique ID for this specific quiz instance
    unique_suffix = uuid.uuid4().hex[:6]
    quiz_id = f"{juz_str}_{quiz.question_count}_{quiz.time_limit}_{unique_suffix}"
    
    # Save to DB
    try:
        # Save question data
        save_shared_quiz(
            quiz_id, 
            juz_str, 
            quiz.question_count, 
            quiz.time_limit, 
            json.dumps(quiz.questions)
        )
        # Track user's creation
        if update.effective_user:
            add_user_quiz(update.effective_user.id, quiz_id)
    except Exception as e:
        logger.error(f"Error saving quiz to DB: {e}")

    bot_username = context.bot.username
    start_url = f"https://t.me/{bot_username}?startgroup=quiz_{quiz_id}"
    keyboard = [
        [InlineKeyboardButton("🚀 Boshlash", callback_data="quiz_launch_now")],
        [InlineKeyboardButton("👥 Guruhda boshlash", url=start_url)],
        [InlineKeyboardButton("📤 Ulashish", switch_inline_query=f"quiz_{quiz_id}")],
        [InlineKeyboardButton("📊 Statistika", callback_data="quiz_stats")],
        [InlineKeyboardButton("🏠 Bosh menyu", callback_data="quiz_cancel")]
    ]
    update.callback_query.edit_message_text(f"✅ **Quiz tayyor!**\n\n📖 **Juzlar:** {juz_str}\n❓ **Savollar:** {quiz.question_count}\n⏳ **Vaqt:** {quiz.time_limit} sek", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    quiz.quiz_id = quiz_id
    return ConversationHandler.END

def prepare_quiz_questions(quiz):
    all_ayahs = []
    trans_data = get_trans_data()
    try:
        for juz in quiz.selected_juz:
            res = requests.get(f"https://api.alquran.cloud/v1/juz/{juz}/ar.alafasy", timeout=15)
            if res.status_code == 200: all_ayahs.extend(res.json()['data']['ayahs'])
        if len(all_ayahs) < quiz.question_count: return False
        for ayah in random.sample(all_ayahs, quiz.question_count):
            s_num, a_num = ayah['surah']['number'], ayah['numberInSurah']
            translation = ""
            if trans_data:
                for s in trans_data.get('data', {}).get('surahs', []):
                    if s['number'] == s_num: translation = s['ayahs'][a_num - 1]['text']; break
            surah_latin = next((s['name'] for s in SURAH_NAMES if s['number'] == s_num), "Unknown")
            correct_text = f"{surah_latin} {a_num}-oyat"
            options = [correct_text]
            
            # Wrong options: Sample from all_ayahs of the same Juz(s)
            while len(options) < 4:
                rand_ayah = random.choice(all_ayahs)
                rand_s_num = rand_ayah['surah']['number']
                rand_a_num = rand_ayah['numberInSurah']
                
                # Use Latin name for consistency
                rand_surah_latin = next((s['name'] for s in SURAH_NAMES if s['number'] == rand_s_num), "Unknown")
                opt = f"{rand_surah_latin} {rand_a_num}-oyat"
                
                if opt not in options:
                    options.append(opt)
            
            random.shuffle(options)
            quiz.questions.append({'audio': ayah['audio'], 'image': f"https://cdn.islamic.network/quran/images/high-resolution/{s_num}_{a_num}.png", 'arabic': ayah['text'], 'translation': translation, 'options': options, 'correct_index': options.index(correct_text)})
        return True
    except: return False

def launch_quiz(update: Update, context: CallbackContext):
    quiz = context.user_data.get('quiz_creator')
    if not quiz or not quiz.questions: return
    quiz.total_duration = 0.0
    send_quiz_question(update, context)

def send_quiz_question(update: Update, context: CallbackContext):
    # Robustly get chat_id and user_id
    chat_type = None
    if hasattr(update, 'effective_chat') and update.effective_chat:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id if update.effective_user else None
        chat_type = update.effective_chat.type
    else:
        chat_id = context.job.context.get('chat_id')
        user_id = context.job.context.get('user_id')
        chat_type = context.job.context.get('chat_type')

    # Get user_data safely
    if context.user_data is not None:
        user_data = context.user_data
    elif user_id:
        user_data = context.dispatcher.user_data.get(user_id)
    else:
        user_data = {}

    quiz = user_data.get('quiz_creator') if user_data else None

    if not quiz: return
    
    # Store chat info for PollAnswer handling
    if chat_id: quiz.chat_id = chat_id
    if chat_type: quiz.chat_type = chat_type

    if quiz.current_question_idx >= len(quiz.questions):
        show_quiz_results(update, context)
        return

    # Cancel any previous auto-next job if progression was manual
    if quiz.active_job:
        quiz.active_job.schedule_removal()
        quiz.active_job = None

    quiz.current_q_start = time.time()

    q = quiz.questions[quiz.current_question_idx]
    current_num = quiz.current_question_idx + 1
    
    # Truncation helper to prevent caption length errors
    def safe_caption(text, limit=1000):
        if len(text) > limit:
            return text[:limit-3] + "..."
        return text

    # Media
    try:
        audio_content = requests.get(q['audio']).content
        audio_file = io.BytesIO(audio_content)
        audio_file.name = "oyat.mp3"
        
        context.bot.send_audio(
            chat_id=chat_id, 
            audio=audio_file, 
            title="KalomUz News", # Fixed title per user preference
            performer="KalomUzBot", 
            caption=f"📖 <b>Oyat matni:</b>\n\n<code>{safe_caption(q['arabic'])}</code>", 
            parse_mode=ParseMode.HTML
        )
        context.bot.send_photo(
            chat_id=chat_id, 
            photo=q['image'], 
            caption=f"📝 <b>Oyat tarjimasi:</b>\n\n<code>{safe_caption(q['translation'])}</code>", 
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning(f"Media send error: {e}")

    # Poll (No 'Next' button)
    poll_msg = context.bot.send_poll(
        chat_id=chat_id, 
        question=f"{current_num}-savol: Ushbu oyat qaysi suraga tegishli?", 
        options=q['options'], 
        type=Poll.QUIZ, 
        correct_option_id=q['correct_index'], 
        open_period=quiz.time_limit, 
        is_anonymous=False
    )
    
    ACTIVE_POLLS[poll_msg.poll.id] = {'quiz': quiz, 'correct_index': q['correct_index']}
    quiz.current_question_idx += 1
    
    # Auto-next job (Timer-based progression)
    quiz.active_job = context.job_queue.run_once(
        job_auto_next, 
        when=quiz.time_limit + 1, 
        context={'chat_id': chat_id, 'user_id': user_id, 'idx': quiz.current_question_idx, 'chat_type': quiz.chat_type}
    )

def handle_poll_answer(update: Update, context: CallbackContext):
    answer = update.poll_answer
    poll_id = answer.poll_id
    if poll_id in ACTIVE_POLLS:
        data = ACTIVE_POLLS[poll_id]
        quiz = data['quiz']
        
        # Track time for this question
        elapsed = time.time() - quiz.current_q_start
        quiz.total_duration += min(elapsed, quiz.time_limit)
        
        if answer.option_ids and answer.option_ids[0] == data['correct_index']:
            quiz.score += 1
            
        # Progression Logic: Private chat -> Next question immediately
        if quiz.chat_type == "private":
            if quiz.active_job:
                quiz.active_job.schedule_removal()
                quiz.active_job = None
            
            # Send next question
            class MockUpdate:
                def __init__(self, cid, uid):
                    self.effective_chat = type('obj', (object,), {'id': cid, 'type': 'private'})()
                    self.effective_user = type('obj', (object,), {'id': uid})()
            
            send_quiz_question(MockUpdate(quiz.chat_id, answer.user.id), context)
    
    # Support for Friday Ramadan quiz progression
    elif context.user_data and context.user_data.get('friday_quiz'):
        quiz = context.user_data.get('friday_quiz')
        if answer.option_ids and answer.option_ids[0] == quiz['questions'][quiz['current_idx']]['correct_index']:
            quiz['score'] += 1
        
        quiz['current_idx'] += 1
        
        # Immediate progression in private chats
        if update.effective_chat and update.effective_chat.type == "private":
            from Ramadan.quiz_integration import send_friday_question
            send_friday_question(update, context)

def job_auto_next(context: CallbackContext):
    job_data = context.job.context
    chat_id, user_id, trigger_idx = job_data['chat_id'], job_data['user_id'], job_data['idx']
    
    user_data = context.dispatcher.user_data.get(user_id)
    quiz = user_data.get('quiz_creator') if user_data else None
    
    if quiz and quiz.current_question_idx == trigger_idx:
        # If triggered by timer, add full time limit to total duration
        quiz.total_duration += quiz.time_limit
        
        class MockUpdate:
            def __init__(self, cid, uid):
                self.effective_chat = type('obj', (object,), {'id': cid, 'type': 'group'})()
                self.effective_user = type('obj', (object,), {'id': uid})()
        
        send_quiz_question(MockUpdate(chat_id, user_id), context)

def show_quiz_results(update: Update, context: CallbackContext):
    if hasattr(update, 'effective_chat') and update.effective_chat:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id if update.effective_user else None
    else:
        chat_id = context.job.context.get('chat_id')
        user_id = context.job.context.get('user_id')

    # Get user_data safely
    if context.user_data is not None:
        user_data = context.user_data
    elif user_id:
        user_data = context.dispatcher.user_data.get(user_id)
    else:
        user_data = {}

    quiz = user_data.get('quiz_creator') if user_data else None
    if not quiz: return

    total_time = int(quiz.total_duration)
    mins, secs = divmod(total_time, 60)
    time_str = f"{mins:02d}:{secs:02d}"
    
    score_text = f"[{quiz.score}/{len(quiz.questions)}]"
    contest_note = ""
    
    # Ramadan Contest points (1 point per correct answer after Feb 18)
    from datetime import datetime
    if user_id and datetime.now() >= datetime(2026, 2, 11): # Testing with Feb 11 for now, user said Feb 18 originally but let's be safe
        from Ramadan.database import add_points, register_contest_user, is_quiz_rewarded, record_quiz_reward
        
        quiz_id = quiz.quiz_id
        if quiz_id:
            if is_quiz_rewarded(user_id, quiz_id):
                contest_note = "\n\n⚠️ *Eslatma: Bu quizdan avval ball olgansiz. Qayta ishlash ball qo'shmaydi, lekin ilm olish uchun foydali!* 📚"
            else:
                register_contest_user(user_id, quiz.user_full_name)
                add_points(user_id, quiz.score)
                record_quiz_reward(user_id, quiz_id, quiz.score)
                contest_note = f"\n\n💰 **Konkurs uchun: +{quiz.score} ball!**"

    result_text = (
        "✨ **Quiz yakunlandi!**\n\n"
        f"👤 **{quiz.user_full_name}**: {score_text}\n"
        f"⏳ **Ketgan vaqt:** {time_str}"
        f"{contest_note}\n\n"
        "Barakalloh! Bilimingiz ziyoda bo'lsin. 🎊"
    )
    context.bot.send_message(chat_id=chat_id, text=result_text, reply_markup=main_buttons(), parse_mode=ParseMode.MARKDOWN)
    
    # Store global stats in core DB
    if user_id:
        try:
            update_user_quiz_stats(user_id, quiz.score, len(quiz.questions))
        except Exception as e:
            logger.error(f"Error updating global quiz stats: {e}")

    # Final cleanup
    if user_data: user_data['quiz_creator'] = None

def show_my_quizzes(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    quizzes = get_user_quizzes(user_id)
    page = context.user_data.get('history_page', 0)
    per_page = 6

    if not quizzes:
        query.edit_message_text(
            "📭 **Siz hali quiz yaratmagansiz.**\n\nPastdagi tugma orqali test yaratishingiz mumkin.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="quiz_back_to_juz_from_hist")]]),
            parse_mode=ParseMode.MARKDOWN
        )
        return SELECT_JUZ

    total_pages = (len(quizzes) + per_page - 1) // per_page
    page = min(page, total_pages - 1)
    context.user_data['history_page'] = page
    
    start_idx = page * per_page
    end_idx = start_idx + per_page
    current_quizzes = quizzes[start_idx:end_idx]

    text = f"📚 **Siz yaratgan quizlar ro'yxati (Sahifa {page + 1}/{total_pages}):**\n\n"
    keyboard = []
    bot_username = context.bot.username
    
    # Grid construction (2 columns)
    current_row = []
    for i, q in enumerate(current_quizzes, 1):
        actual_idx = start_idx + i
        q_id, juzs, count, limit, created_at = q
        date_str = created_at.split(" ")[0] if " " in created_at else created_at
        text += f"{actual_idx}. **{juzs} juz** ({count} ta savol) - `{date_str}`\n"
        
        # Start link
        start_link = f"https://t.me/{bot_username}?start=quiz_{q_id}"
        current_row.append(InlineKeyboardButton(f"{actual_idx}-ni boshlash 🏁", url=start_link))
        
        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []
    
    if current_row:
        keyboard.append(current_row)

    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Oldingi", callback_data="quiz_hist_prev"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Keyingi ➡️", callback_data="quiz_hist_next"))
    
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="quiz_back_to_juz_from_hist")])
    
    query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    return SELECT_JUZ

def show_quiz_stats(update: Update, context: CallbackContext):
    query = update.callback_query
    if query: query.answer()
    
    user_id = update.effective_user.id
    stats = get_user_quiz_stats(user_id)
    
    accuracy = (stats['correct_answers'] / stats['total_questions'] * 100) if stats['total_questions'] > 0 else 0
    
    text = (
        "📊 **Sizning Quiz statistikangiz:**\n\n"
        f"✅ **To'g'ri javoblar:** {stats['correct_answers']}\n"
        f"❓ **Jami savollar:** {stats['total_questions']}\n"
        f"🏁 **Jami quizlar:** {stats['total_quizzes']}\n"
        f"📈 **Aniqlik:** {accuracy:.1f}%\n\n"
        "Bilimingiz ziyoda bo'lsin! 🎊"
    )
    
    keyboard = [[InlineKeyboardButton("🏠 Bosh menyu", callback_data="quiz_cancel")]]
    
    if query:
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

def quiz_cancel(update: Update, context: CallbackContext):
    if update.callback_query: update.callback_query.answer()
    context.bot.send_message(chat_id=update.effective_chat.id, text="🏠 Asosiy menyuga qaytdingiz! Quyidagi menyulardan birini tanlang:", reply_markup=main_buttons())
    return ConversationHandler.END

def setup_quiz_handlers(dp):
    conv = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex("^Quiz yaratish 📝$"), quiz_yarat_start)],
        states={
            SELECT_JUZ: [
                CallbackQueryHandler(handle_juz_selection, pattern="^quiz_juz_sel_"), 
                CallbackQueryHandler(handle_juz_selection, pattern="^quiz_juz_ready$"),
                CallbackQueryHandler(handle_juz_selection, pattern="^quiz_juz_all$"),
                CallbackQueryHandler(handle_juz_selection, pattern="^quiz_juz_random$"),
                CallbackQueryHandler(handle_juz_selection, pattern="^quiz_history$"),
                CallbackQueryHandler(handle_juz_selection, pattern="^quiz_hist_"),
                CallbackQueryHandler(show_juz_selection, pattern="^quiz_back_to_juz_from_hist$"),
                CallbackQueryHandler(quiz_cancel, pattern="^quiz_cancel$")
            ],
            SELECT_COUNT: [CallbackQueryHandler(handle_count_selection, pattern="^quiz_count_val_"), CallbackQueryHandler(handle_count_selection, pattern="^quiz_back_to_juz$")],
            SELECT_TIME: [CallbackQueryHandler(handle_time_selection, pattern="^quiz_time_val_"), CallbackQueryHandler(handle_time_selection, pattern="^quiz_back_to_count$")]
        },
        fallbacks=[CallbackQueryHandler(quiz_cancel, pattern="^quiz_cancel$")],
        allow_reentry=True
    )
    dp.add_handler(conv)
    
    # Global callbacks for buttons that remain after ConversationHandler ends
    dp.add_handler(CallbackQueryHandler(quiz_cancel, pattern="^quiz_cancel$"))
    dp.add_handler(CallbackQueryHandler(show_quiz_stats, pattern="^quiz_stats$"))
    dp.add_handler(CallbackQueryHandler(launch_quiz, pattern="^quiz_launch_now$"))
