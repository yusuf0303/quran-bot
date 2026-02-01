from telegram import Update, Poll, ParseMode, PollAnswer
from telegram.ext import CallbackContext
from Ramadan.database import add_points, DB_PATH
from Suralarni_toping.surahs import SURAH_NAMES
from Suralarni_toping.database import DB_PATH as QURAN_DB_PATH
import time

def generate_friday_quiz_questions():
    # Fetch all ayahs from Quran DB (Suralarni_toping/Quran_Database.db)
    conn = sqlite3.connect(QURAN_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, surah_id, ayah_id, content FROM ayahs")
    all_ayahs = cursor.fetchall()
    conn.close()
    
    # Select 20 random ayahs
    selected_ayahs = random.sample(all_ayahs, 20)
    
    # Load translation
    trans_path = os.path.join("Suralarni_toping", "quran_trans_uz.json")
    with open(trans_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    questions = []
    for ayah in selected_ayahs:
        ayah_id_in_db, surah_id, ayah_id, content = ayah
        correct_surah = SURAH_NAMES.get(surah_id, "Noma'lum")
        
        # Distractors from all surahs
        all_surah_names = list(SURAH_NAMES.values())
        if correct_surah in all_surah_names: all_surah_names.remove(correct_surah)
        distractors = random.sample(all_surah_names, 3)
        
        options = distractors + [correct_surah]
        random.shuffle(options)
        correct_idx = options.index(correct_surah)
        
        # Get translation
        trans_key = f"{surah_id}:{ayah_id}"
        translation = translations.get(trans_key, "")
        
        questions.append({
            'surah_id': surah_id,
            'ayah_id': ayah_id,
            'content': content,
            'translation': translation,
            'options': options,
            'correct_index': correct_idx
        })
    
    return questions

def start_friday_quiz(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Register session in user_data
    questions = generate_friday_quiz_questions()
    context.user_data['friday_quiz'] = {
        'questions': questions,
        'current_idx': 0,
        'score': 0,
        'start_time': time.time(),
        'time_limit': 30,
        'active_job': None
    }
    
    update.message.reply_text("🌟 **Juma Testi boshlanmoqda!**\nSizga 20 ta random savol beriladi. Har bir to'g'ri javob uchun 5 ball! Omad! 🚀", parse_mode=ParseMode.MARKDOWN)
    send_friday_question(update, context)

def send_friday_question(update: Update, context: CallbackContext):
    quiz_data = context.user_data.get('friday_quiz')
    if not quiz_data: return
    
    idx = quiz_data['current_idx']
    if idx >= len(quiz_data['questions']):
        finish_friday_quiz(update, context)
        return
    
    q = quiz_data['questions'][idx]
    
    # Send as poll
    msg = context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=f"Bu oyat qaysi suradan? ({idx+1}/20)",
        options=q['options'],
        type=Poll.QUIZ,
        correct_option_id=q['correct_index'],
        is_anonymous=False,
        explanation=f"To'g'ri javob: {q['options'][q['correct_index']]} surasi."
    )
    
    context.user_data['last_friday_poll'] = msg.poll.id
    
    # Auto-next job for Friday quiz (Timer-based progression)
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Cancel previous job
    if quiz_data.get('active_job'):
        quiz_data['active_job'].schedule_removal()

    quiz_data['active_job'] = context.job_queue.run_once(
        job_friday_auto_next,
        when=quiz_data['time_limit'] + 1,
        context={'chat_id': chat_id, 'user_id': user_id, 'idx': idx}
    )

def job_friday_auto_next(context: CallbackContext):
    job_data = context.job.context
    chat_id, user_id, trigger_idx = job_data['chat_id'], job_data['user_id'], job_data['idx']
    
    user_data = context.dispatcher.user_data.get(user_id)
    quiz = user_data.get('friday_quiz') if user_data else None
    
    if quiz and quiz['current_idx'] == trigger_idx:
        quiz['current_idx'] += 1
        
        class MockUpdate:
            def __init__(self, cid, uid):
                self.effective_chat = type('obj', (object,), {'id': cid, 'type': 'group'})()
                self.effective_user = type('obj', (object,), {'id': uid})()
        
        send_friday_question(MockUpdate(chat_id, user_id), context)
    
from datetime import datetime

def finish_friday_quiz(update: Update, context: CallbackContext):
    quiz_data = context.user_data.get('friday_quiz')
    if not quiz_data: return
    
    score = quiz_data['score']
    points = score * 5
    
    # Calculate time
    total_seconds = int(time.time() - quiz_data['start_time'])
    mins, secs = divmod(total_seconds, 60)
    time_str = f"{mins:02d}:{secs:02d}"
    
    user_id = update.effective_user.id
    
    # Anti-cheat: Friday quiz ID based on date (e.g., friday_2026_02_13)
    friday_id = f"friday_{datetime.now().strftime('%Y_%m_%d')}"
    
    from Ramadan.database import add_points, is_quiz_rewarded, record_quiz_reward, register_contest_user
    
    contest_note = ""
    if is_quiz_rewarded(user_id, friday_id):
        contest_note = "\n\n⚠️ *Eslatma: Bu haftalik juma testidan avval ball olgansiz. Qayta ishlash ball qo'shmaydi, lekin ilm olish uchun foydali!* 📚"
    else:
        register_contest_user(user_id, update.effective_user.full_name)
        add_points(user_id, points)
        record_quiz_reward(user_id, friday_id, score, quiz_type='friday')
        contest_note = f"\n\n💰 **Konkurs uchun: +{points} ball!**"
    
    update.message.reply_text(
        f"🏁 **Juma Testi yakunlandi!**\n\n"
        f"👤 {update.effective_user.full_name}\n"
        f"✅ To'g'ri javoblar: {score}/20\n"
        f"⏳ Ketgan vaqt: {time_str}"
        f"{contest_note}\n\n"
        "Barakalloh! Bilimingiz ziyoda bo'lsin. 🎊",
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['friday_quiz'] = None
