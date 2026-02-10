import os
from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    upsert_specialist,
    get_conversation_by_specialist_message,
    get_user_by_conversation,
    save_message,
    is_specialist,
)

router = Router()

ALLOWED_CATEGORIES = {"admin1", "admin2", "admin3", "admin4"}


def _parse_admin_ids(raw: str | None) -> set[int]:
    """
    ADMIN_IDS="123,456 789" kabi qiymatlarni ham ko'taradi.
    """
    if not raw:
        return set()
    parts = raw.replace(" ", ",").split(",")
    out: set[int] = set()
    for p in parts:
        p = p.strip()
        if not p:
            continue
        try:
            out.add(int(p))
        except ValueError:
            pass
    return out


ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS"))
REGISTER_SECRET = os.getenv("REGISTER_SECRET")


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _help_text() -> str:
    return (
        "Ro'yxatdan o'tish:\n"
        "/register <kategoriya> <secret>\n\n"
        "Kategoriyalar: admin1 | admin2 | admin3 | admin4\n"
        "Misol: /register admin1 MySecret123"
    )


@router.message(Command("register"))
async def cmd_register(message: Message):
    """
    Himoyalangan register:
    - Faqat ADMIN_IDS ichidagi adminlar ishlata oladi
    - Va albatta REGISTER_SECRET ham to'g'ri bo'lishi kerak
    """
    if not ADMIN_IDS:
        await message.answer("❌ ADMIN_IDS sozlanmagan (.env). Adminlar ro'yxatini kiriting.")
        return
    if not REGISTER_SECRET:
        await message.answer("❌ REGISTER_SECRET sozlanmagan (.env). Secret token kiriting.")
        return

    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu buyruqni ishlatish huquqi yo'q.")
        return

    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(_help_text())
        return

    category = parts[1].strip().lower()
    secret = parts[2].strip()

    if category not in ALLOWED_CATEGORIES:
        await message.answer(
            "❌ Noto'g'ri kategoriya.\n"
            "Mavjud: admin1 | admin2 | admin3 | admin4"
        )
        return

    if secret != REGISTER_SECRET:
        await message.answer("⛔ Secret noto'g'ri.")
        return

    specialist_chat_id = message.chat.id
    username = message.from_user.username
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() or None

    await upsert_specialist(category, specialist_chat_id, username, full_name)

    await message.answer(
        "✅ Mutaxassis ro'yxatdan o'tkazildi.\n"
        f"Kategoriya: {category}\n"
        f"chat_id: {specialist_chat_id}\n\n"
        "Eslatma: agar boshqa odamni ro'yxatdan o'tkazmoqchi bo'lsangiz, "
        "u odam botga o'zi yozib (kamida /start) chat ochgan bo'lishi kerak va "
        "register o'sha chatda bajariladi."
    )


# ✅ MUHIM: Mutaxassisning javobini tutish
# Filter: reply_to_message mavjud bo'lishi kerak
@router.message(F.reply_to_message)
async def handle_specialist_reply(message: Message, bot: Bot):
    """
    Mutaxassis reply qilganda, userga javob yuboradi
    """
    specialist_chat_id = message.chat.id

    # Tekshirish: bu mutaxassismi?
    if not await is_specialist(specialist_chat_id):
        # Oddiy user, keyingi handler bilan ishlaydi
        return

    # Reply qilingan xabarning IDsi
    replied_message_id = message.reply_to_message.message_id

    # Bu xabar qaysi conversation'ga tegishli?
    conversation_id = await get_conversation_by_specialist_message(replied_message_id)
    if not conversation_id:
        await message.answer("❌ Bu xabar hech qaysi suhbatga tegishli emas.")
        return

    # Userning chat_id'sini topamiz
    user_id = await get_user_by_conversation(conversation_id)
    if not user_id:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    # Javobni saqlash
    await save_message(conversation_id, "specialist", message.text, message.message_id)

    # Userga javobni yuborish
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"💬 Mutaxassis javobi:\n\n{message.text}"
        )
        await message.answer("✅ Javob yuborildi.")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {e}")
        print(f"Error sending to user {user_id}: {e}")