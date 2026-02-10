import os
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def get_category_keyboard():
    """
    .env faylidan mutaxassislarni olib kelib, ism-familiya bilan tugmalar yasaydi
    """
    from database import get_all_specialists

    # Database'dan barcha mutaxassislarni olamiz
    specialists = await get_all_specialists()

    if not specialists:
        # Agar hech kim ro'yxatdan o'tmagan bo'lsa
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Mutaxassislar mavjud emas")]],
            resize_keyboard=True
        )

    buttons = []
    for spec in specialists:
        full_name = spec['full_name']
        category = spec['category']

        if full_name:
            button_text = f"👤 {full_name}"
        else:
            # Agar database'da ism yo'q bo'lsa, .env dan olamiz
            env_name = os.getenv(f"SPECIALIST_{category.upper()}_NAME")
            if env_name:
                button_text = f"👤 {env_name}"
            else:
                button_text = f"👤 {category.upper()}"

        buttons.append(KeyboardButton(text=button_text))

    # 2 ustunli qilib joylashtirish
    keyboard_layout = []
    for i in range(0, len(buttons), 2):
        row = buttons[i:i + 2]
        keyboard_layout.append(row)

    keyboard = ReplyKeyboardMarkup(
        keyboard=keyboard_layout,
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