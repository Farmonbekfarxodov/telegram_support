from aiogram import Router, F, Bot
from aiogram.types import Message

from database import (
    get_active_conversation,
    save_message,
    save_message_mapping,
    save_contact,
    get_user_phone,
)
from keyboards import get_contact_keyboard, get_category_keyboard

router = Router()


@router.message(F.contact)
async def handle_contact(message: Message):
    user_id = message.from_user.id
    phone = message.contact.phone_number

    await save_contact(user_id, phone)

    await message.answer(
        "✅ Kontaktingiz saqlandi.\n",
        reply_markup=await get_category_keyboard()  # ✅ await qo'shildi
    )


@router.message(F.text)
async def handle_user_message(message: Message, bot: Bot):
    user_id = message.from_user.id

    conv = await get_active_conversation(user_id)
    if not conv:
        await message.answer(
            "❌ Avval bo'limni tanlang (/start).",
            reply_markup=await get_category_keyboard()  # ✅ await qo'shildi
        )
        return

    conversation_id, specialist_chat_id = conv

    await save_message(conversation_id, "user", message.text, message.message_id)

    try:
        specialist_msg = await bot.send_message(
            chat_id=specialist_chat_id,
            text=(
                f"📩 Yangi xabar (#{conversation_id}):\n\n"
                f"👤 {message.from_user.first_name} (@{message.from_user.username or 'no_username'})\n\n"
                f"💬 {message.text}\n\n"
                f"Javob berish uchun shu xabarga reply qiling."
            ),
        )

        await save_message_mapping(
            specialist_msg.message_id,
            conversation_id,
            message.message_id
        )

        # ✅ Kontakt faqat 1-marta so'raladi
        phone = await get_user_phone(user_id)
        if not phone:
            await message.answer(
                "✅ Yuborildi. Biz siz bilan bog'lanishimiz uchun kontaktingizni qoldiring:",
                reply_markup=get_contact_keyboard()
            )
        else:
            await message.answer("✅ Yuborildi.")

    except Exception as e:
        await message.answer("❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.")
        print(f"Error: {e}")