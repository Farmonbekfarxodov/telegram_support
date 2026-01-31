from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from keyboards import get_category_keyboard
from database import save_user, create_conversation, get_specialist_chat_id_by_category

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    await save_user(user.id, user.username, user.first_name)

    await message.answer(
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        reply_markup=get_category_keyboard()
    )


CATEGORY_MAP = {
    "📞 Texnik Yordam": "texnik",
    "💼 Savdo Bo'limi": "savdo",
    "📊 Konsultatsiya": "konsultatsiya",
    "⚙️ Boshqa": "boshqa"
}


@router.message(F.text.in_(CATEGORY_MAP.keys()))
async def handle_category_selection(message: Message):
    user_id = message.from_user.id
    category = CATEGORY_MAP[message.text]

    # Mutaxassisni DB'dan topamiz (production register)
    specialist_chat_id = await get_specialist_chat_id_by_category(category)

    if not specialist_chat_id:
        await message.answer(
            "❌ Bu bo'lim uchun mutaxassis hali ro'yxatdan o'tmagan.\n\n"
            "Iltimos, boshqa bo'limni tanlang yoki keyinroq urinib ko'ring.",
            reply_markup=get_category_keyboard()
        )
        return

    await create_conversation(user_id, category, specialist_chat_id)

    await message.answer(
        f"✅ {message.text} tanlandi.\n\n"
        "Savolingizni yozing 👇"
    )