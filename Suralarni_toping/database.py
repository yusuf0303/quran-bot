import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "ayah_game.db"

DB_FOLDER = DB_PATH.parent
def init_db():
    DB_FOLDER.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        registered_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        correct_answers INTEGER DEFAULT 0,
        total_attempts INTEGER DEFAULT 0,
        last_played TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    """)

    conn.commit()
    conn.close()


def get_user_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT correct_answers, total_attempts 
    FROM game_stats 
    WHERE user_id = ?
    """, (user_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {'correct_answers': result[0], 'total_attempts': result[1]}
    return {'correct_answers': 0, 'total_attempts': 0}


def update_user_stats(user_id, correct_answer=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM game_stats WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()

    if exists:
        if correct_answer:
            cursor.execute("""
            UPDATE game_stats 
            SET correct_answers = correct_answers + 1,
                total_attempts = total_attempts + 1,
                last_played = ?
            WHERE user_id = ?
            """, (datetime.now().isoformat(), user_id))
        else:
            cursor.execute("""
            UPDATE game_stats 
            SET total_attempts = total_attempts + 1,
                last_played = ?
            WHERE user_id = ?
            """, (datetime.now().isoformat(), user_id))
    else:
        if correct_answer:
            cursor.execute("""
            INSERT INTO game_stats (user_id, correct_answers, total_attempts, last_played)
            VALUES (?, 1, 1, ?)
            """, (user_id, datetime.now().isoformat()))
        else:
            cursor.execute("""
            INSERT INTO game_stats (user_id, correct_answers, total_attempts, last_played)
            VALUES (?, 0, 1, ?)
            """, (user_id, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def register_user(user):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    """, (user.id, user.username, user.first_name, user.last_name or ""))

    conn.commit()
    conn.close()


def get_top_10_users():
    """Eng yaxshi 10 o'yinchini olish"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT u.first_name, u.username, g.correct_answers, g.total_attempts,
           (g.correct_answers * 100.0 / g.total_attempts) as accuracy
    FROM game_stats g
    JOIN users u ON g.user_id = u.user_id
    WHERE g.total_attempts >= 5  
    ORDER BY accuracy DESC, g.correct_answers DESC
    LIMIT 10
    """)

    results = cursor.fetchall()
    conn.close()

    return results


def get_user_rank(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT (correct_answers * 100.0 / total_attempts) as accuracy
    FROM game_stats
    WHERE user_id = ? AND total_attempts >= 5
    """, (user_id,))

    user_accuracy = cursor.fetchone()
    if not user_accuracy:
        return None

    cursor.execute("""
    SELECT COUNT(*) + 1 as rank
    FROM game_stats
    WHERE (correct_answers * 100.0 / total_attempts) > ? 
      AND total_attempts >= 5
    """, (user_accuracy[0],))

    rank = cursor.fetchone()[0]
    conn.close()

    return rank


def get_user_position(user_id):
    """Foydalanuvchi haqida to'liq ma'lumot (o'zi va uning atrofidagi 2ta o'yinchi)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    WITH ranked_users AS (
        SELECT 
            u.user_id,
            u.first_name,
            g.correct_answers,
            g.total_attempts,
            (g.correct_answers * 100.0 / g.total_attempts) as accuracy,
            ROW_NUMBER() OVER (ORDER BY (g.correct_answers * 100.0 / g.total_attempts) DESC) as rank
        FROM game_stats g
        JOIN users u ON g.user_id = u.user_id
        WHERE g.total_attempts >= 5
    )
    SELECT * FROM ranked_users
    ORDER BY rank
    """)

    all_users = cursor.fetchall()

    current_user = None
    for i, user in enumerate(all_users):
        if user[0] == user_id:
            current_user = user
            break

    if not current_user:
        conn.close()
        return None

    start_idx = max(0, i - 1)
    end_idx = min(len(all_users), i + 2)
    nearby_users = all_users[start_idx:end_idx]

    conn.close()
    return {
        'current_user': current_user,
        'nearby_users': nearby_users,
        'total_players': len(all_users)
    }


def get_all_user_ids():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT user_id FROM users")
    result = c.fetchall()
    conn.close()
    return [row[0] for row in result]