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
from Suralarni_toping.database import save_shared_quiz, get_shared_quiz, add_user_quiz, get_user_quizzes

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
        self.start_timestamp = 0
        self.user_full_name = ""

def quiz_yarat_start(update: Update, context: CallbackContext):
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
    quiz.start_timestamp = time.time()
    send_quiz_question(update, context)

def send_quiz_question(update: Update, context: CallbackContext):
    # Robustly get chat_id and user_id
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
    if quiz.current_question_idx >= len(quiz.questions):
        show_quiz_results(update, context)
        return

    q = quiz.questions[quiz.current_question_idx]
    current_num = quiz.current_question_idx + 1
    
    # Media
    try:
        audio_content = requests.get(q['audio']).content
        audio_file = io.BytesIO(audio_content)
        audio_file.name = "oyat.mp3"
        
        context.bot.send_audio(
            chat_id=chat_id, 
            audio=audio_file, 
            title="Sura nomi yashirin",
            performer="KalomUzBot", 
            caption=f"📖 **Oyat matni:**\n\n{q['arabic']}", 
            parse_mode=ParseMode.MARKDOWN
        )
        context.bot.send_photo(
            chat_id=chat_id, 
            photo=q['image'], 
            caption=f"📝 **Oyat tarjimasi:**\n\n{q['translation']}", 
            parse_mode=ParseMode.MARKDOWN
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
    context.job_queue.run_once(
        job_auto_next, 
        when=quiz.time_limit + 1, 
        context={'chat_id': chat_id, 'user_id': user_id, 'idx': quiz.current_question_idx}
    )

def handle_poll_answer(update: Update, context: CallbackContext):
    answer = update.poll_answer
    poll_id = answer.poll_id
    if poll_id in ACTIVE_POLLS:
        data = ACTIVE_POLLS[poll_id]
        quiz = data['quiz']
        if answer.option_ids and answer.option_ids[0] == data['correct_index']:
            quiz.score += 1

def job_auto_next(context: CallbackContext):
    job_data = context.job.context
    chat_id, user_id, trigger_idx = job_data['chat_id'], job_data['user_id'], job_data['idx']
    
    user_data = context.dispatcher.user_data.get(user_id)
    quiz = user_data.get('quiz_creator') if user_data else None
    
    if quiz and quiz.current_question_idx == trigger_idx:
        class MockUpdate:
            def __init__(self, cid, uid):
                self.effective_chat = type('obj', (object,), {'id': cid})()
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

    total_time = int(time.time() - quiz.start_timestamp)
    mins, secs = divmod(total_time, 60)
    time_str = f"{mins:02d}:{secs:02d}"
    
    result_text = (
        "✨ **Quiz yakunlandi!**\n\n"
        f"👤 **{quiz.user_full_name}**: [{quiz.score}/{len(quiz.questions)}]\n"
        f"⏳ **Ketgan vaqt:** {time_str}\n\n"
        "Barakalloh! Bilimingiz ziyoda bo'lsin. 🎊"
    )
    context.bot.send_message(chat_id=chat_id, text=result_text, reply_markup=main_buttons(), parse_mode=ParseMode.MARKDOWN)
    
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
    dp.add_handler(CallbackQueryHandler(launch_quiz, pattern="^quiz_launch_now$"))
