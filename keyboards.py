from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_category_keyboard():
    """4 ta kategoriya tugmalari"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Texnik Yordam"), KeyboardButton(text="💼 Savdo Bo'limi")],
            [KeyboardButton(text="📊 Konsultatsiya"), KeyboardButton(text="⚙️ Boshqa")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_contact_keyboard():
    """Kontakt yuborish tugmasi"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Kontaktni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard