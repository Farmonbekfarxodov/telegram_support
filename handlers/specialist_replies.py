import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import upsert_specialist

router = Router()

ALLOWED_CATEGORIES = {"texnik", "savdo", "konsultatsiya", "boshqa"}


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
            # noto'g'ri bo'laklarni e'tiborsiz qoldiramiz
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
        "Kategoriyalar: texnik | savdo | konsultatsiya | boshqa\n"
        "Misol: /register texnik MySecret123"
    )


@router.message(Command("register"))
async def cmd_register(message: Message):
    """
    Himoyalangan register:
    - Faqat ADMIN_IDS ichidagi adminlar ishlata oladi
    - Va albatta REGISTER_SECRET ham to'g'ri bo'lishi kerak

    Komanda:
      /register texnik MySecret123

    Natija:
      specialists jadvalida shu category uchun chat_id = mutaxassis_id bo'lib saqlanadi.
    """
    # Konfiguratsiya tekshiruvi
    if not ADMIN_IDS:
        await message.answer("❌ ADMIN_IDS sozlanmagan (.env). Adminlar ro'yxatini kiriting.")
        return
    if not REGISTER_SECRET:
        await message.answer("❌ REGISTER_SECRET sozlanmagan (.env). Secret token kiriting.")
        return

    # Admin tekshiruvi
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu buyruqni ishlatish huquqi yo'q.")
        return

    # Argumentlarni o'qish
    # /register <category> <secret>
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(_help_text())
        return

    category = parts[1].strip().lower()
    secret = parts[2].strip()

    if category not in ALLOWED_CATEGORIES:
        await message.answer(
            "❌ Noto'g'ri kategoriya.\n"
            "Mavjud: texnik, savdo, konsultatsiya, boshqa"
        )
        return

    if secret != REGISTER_SECRET:
        await message.answer("⛔ Secret noto'g'ri.")
        return

    # Bu yerda muhim savol: kimni ro'yxatdan o'tkazyapmiz?
    #
    # 1) Admin o'zi mutaxassis bo'lsa: adminning o'zi yozsa ham bo'ladi.
    # 2) Admin mutaxassisni chatda yo'naltirib ro'yxatdan o'tkazmoqchi bo'lsa:
    #    eng sodda yo'l — mutaxassisning o'zi botga yozib /start qilishi va
    #    admin esa undan keyin (mutaxassisning chatidan) /register ishlatishi.
    #
    # Shuning uchun chat_id sifatida message.chat.id ishlatamiz.
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