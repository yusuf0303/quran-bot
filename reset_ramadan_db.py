import sqlite3
import os

DB_PATH = os.path.join("Ramadan", "ramadan.db")

def reset_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Reset points for all users
        cursor.execute("UPDATE contest_users SET points = 0")
        print("✅ Contest points reset to 0.")
        
        # Clear quiz history (optional, but requested "test vaqtida to'plangan")
        # Checking if user wants to keep history but just reset points?
        # "tets vaqtida to'plangan ball lar o'chirib yuborilishi kerak"
        # Usually implies resetting history too so they can earn points again if needed, 
        # or at least removing the records that gave those points.
        # Safest is to clear quiz_history as well so they can theoretically retake if it was just testing.
        cursor.execute("DELETE FROM quiz_history")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='quiz_history'")
        print("✅ Quiz history cleared.")
        
        conn.commit()
        print("Successfully cleaned up test data.")
    except Exception as e:
        print(f"Error cleaning DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_db()
