import logging
from telegram import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


import os

def main_buttons(user_id=None):
    keyboard = [
        [KeyboardButton("Eng yaqin Masjid 📍", request_location=True)],
        ["Suralar 🔍", "Oyatlarni toping 🔍"],
        ["Masjidlar 🕌", "Namoz vaqtlari 🧎‍♂️"],
        ["Quiz yaratish 📝", "Konkurs 🏆"]
    ]
    
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if user_id and user_id == admin_id:
        keyboard.append(["Xabar yuborish 📤"])
        
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
