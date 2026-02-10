from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from keyboards import get_category_keyboard
from database import save_user, create_conversation, get_specialist_by_full_name

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    await save_user(user.id, user.username, user.first_name)

    keyboard = await get_category_keyboard()  # ✅ await qo'shildi
    await message.answer(
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "Quyidagi mutaxassislardan birini tanlang:",
        reply_markup=keyboard
    )


@router.message(F.text.startswith("👤 "))
async def handle_category_selection(message: Message):
    user_id = message.from_user.id

    # "👤 Alisher Valiyev" dan "Alisher Valiyev" ni ajratib olamiz
    full_name = message.text.replace("👤 ", "").strip()

    # Database'dan shu ism-familiya bo'yicha mutaxassisni topamiz
    specialist = await get_specialist_by_full_name(full_name)

    if not specialist:
        await message.answer(
            "❌ Mutaxassis topilmadi.\n\n"
            "Iltimos, qaytadan tanlang:",
            reply_markup=await get_category_keyboard()  # ✅ await qo'shildi
        )
        return

    category = specialist['category']
    specialist_chat_id = specialist['chat_id']

    await create_conversation(user_id, category, specialist_chat_id)

    await message.answer(
        f"✅ {message.text} tanlandi.\n\n"
        "Savolingizni yozing 👇"
    )