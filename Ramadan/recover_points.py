
import sqlite3
import os

# Database path (adjust if running from different location)
DB_PATH = os.path.join(os.path.dirname(__file__), "ramadan.db")

def recover_missing_points():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: {DB_PATH} topilmadi!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 Tekshirilmoqda...")

    # 1. Barcha tasdiqlangan referallarni olish
    cursor.execute("SELECT referrer_id, COUNT(*) FROM referrals WHERE is_verified = 1 GROUP BY referrer_id")
    verified_referrals = cursor.fetchall()

    fixed_count = 0
    total_points_restored = 0

    for referrer_id, actual_count in verified_referrals:
        # 2. Ishtirokchining hozirgi holatini tekshirish
        cursor.execute("SELECT referrals_count, points, full_name FROM contest_users WHERE user_id = ?", (referrer_id,))
        user = cursor.fetchone()

        if user:
            current_count, current_points, name = user
            if actual_count > current_count:
                diff = actual_count - current_count
                restored_points = diff * 10
                
                # Ballarni va sanog'ini yangilash
                cursor.execute("UPDATE contest_users SET points = points + ?, referrals_count = ? WHERE user_id = ?", 
                               (restored_points, actual_count, referrer_id))
                
                print(f"✅ {name} (ID: {referrer_id}): {diff} ta referal uchun {restored_points} ball qaytarildi.")
                fixed_count += 1
                total_points_restored += restored_points
        else:
            # Foydalanuvchi umuman contest_users tableda yo'q
            restored_points = actual_count * 10
            cursor.execute("INSERT INTO contest_users (user_id, full_name, points, referrals_count) VALUES (?, ?, ?, ?)",
                           (referrer_id, "Ishtirokchi", restored_points, actual_count))
            
            print(f"✅ Yangi foydalanuvchi ID {referrer_id}: {actual_count} ta referal uchun {restored_points} ball bilan qo'shildi.")
            fixed_count += 1
            total_points_restored += restored_points

    conn.commit()
    conn.close()

    print("\n" + "="*30)
    print(f"🎉 Natija:")
    print(f"👤 Yangilangan ishtirokchilar: {fixed_count}")
    print(f"💰 Jami qaytarilgan ballar: {total_points_restored}")
    print("="*30)

if __name__ == "__main__":
    recover_missing_points()
