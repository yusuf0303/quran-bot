#!/usr/bin/env python3
"""
Migration script to add 'confirmed' column to existing users table.
This ensures existing users don't lose access after the update.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "Suralarni_toping" / "ayah_game.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'confirmed' not in columns:
        print("Adding 'confirmed' column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN confirmed INTEGER DEFAULT 1")
        conn.commit()
        print("✅ Migration completed! All existing users are marked as confirmed.")
    else:
        print("⚠️  'confirmed' column already exists. Skipping migration.")
    
    conn.close()

if __name__ == "__main__":
    migrate()
