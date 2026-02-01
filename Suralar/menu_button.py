import logging
from telegram import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main_buttons():
    keyboard = [
        [KeyboardButton("Eng yaqin Masjid 📍", request_location=True)],
        ["Suralar 🔍", "Oyatlarni toping 🔍"],
        ["Masjidlar 🕌", "Namoz vaqtlari 🧎‍♂️"],
        ["Quiz yaratish 📝"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
