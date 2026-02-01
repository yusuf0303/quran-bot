import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "ramadan.db")

def init_ramadan_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # User stats for contest
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contest_users (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        points INTEGER DEFAULT 0,
        region TEXT,
        referrals_count INTEGER DEFAULT 0,
        has_joined_bonus INTEGER DEFAULT 0,
        instagram_claimed INTEGER DEFAULT 0,
        last_friday_quiz TEXT
    )
    """)
    
    # Referral tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS referrals (
        referrer_id INTEGER,
        referred_id INTEGER,
        is_verified INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (referrer_id, referred_id)
    )
    """)
    
    # Quiz attempts tracking
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        quiz_id TEXT,
        quiz_type TEXT, -- 'custom' or 'friday'
        score INTEGER,
        date TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def get_contest_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contest_users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def register_contest_user(user_id, full_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO contest_users (user_id, full_name) VALUES (?, ?)", (user_id, full_name))
    conn.commit()
    conn.close()

def add_points(user_id, points):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE contest_users SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()

def add_referral(referrer_id, referred_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)", (referrer_id, referred_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def verify_referral(referred_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Find referrer
    cursor.execute("SELECT referrer_id FROM referrals WHERE referred_id = ? AND is_verified = 0", (referred_id,))
    result = cursor.fetchone()
    if result:
        referrer_id = result[0]
        cursor.execute("UPDATE referrals SET is_verified = 1 WHERE referred_id = ?", (referred_id,))
        cursor.execute("UPDATE contest_users SET points = points + 10, referrals_count = referrals_count + 1 WHERE user_id = ?", (referrer_id,))
        conn.commit()
        conn.close()
        return referrer_id
    conn.close()
    return None

def get_leaderboard(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, points FROM contest_users ORDER BY points DESC LIMIT ?", (limit,))
    leaders = cursor.fetchall()
    conn.close()
    return leaders

def is_quiz_rewarded(user_id, quiz_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM quiz_history WHERE user_id = ? AND quiz_id = ?", (user_id, quiz_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def record_quiz_reward(user_id, quiz_id, score, quiz_type='custom'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quiz_history (user_id, quiz_id, quiz_type, score) VALUES (?, ?, ?, ?)", (user_id, quiz_id, quiz_type, score))
    conn.commit()
    conn.close()

# Initialize on import
init_ramadan_db()
