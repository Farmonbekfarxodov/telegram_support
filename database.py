import os
import asyncpg
from typing import Optional
from dotenv import load_dotenv  # ✅ Qo'shildi

# ✅ .env faylini yuklash
load_dotenv()

# PostgreSQL ulanish ma'lumotlari (.env / env'dan olinadi)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "support_bot"),
}

_pool: Optional[asyncpg.Pool] = None


async def init_db():
    """
    asyncpg connection pool yaratish va jadvallarni yaratish.
    """
    global _pool
    _pool = await asyncpg.create_pool(**DB_CONFIG, min_size=1, max_size=20)

    async with _pool.acquire() as conn:
        # Foydalanuvchilar
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                phone VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')

        # Suhbatlar
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                category VARCHAR(50),
                specialist_chat_id BIGINT,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')

        # Xabarlar
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id),
                from_role VARCHAR(20),
                message_text TEXT,
                telegram_message_id BIGINT,
                sent_at TIMESTAMP DEFAULT NOW()
            )
        ''')

        # Message mapping (mutaxassis reply → conversation)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS message_mapping (
                specialist_message_id BIGINT PRIMARY KEY,
                conversation_id INTEGER REFERENCES conversations(id),
                user_message_id BIGINT
            )
        ''')

        # Mutaxassislar jadvali
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS specialists (
                category VARCHAR(50) PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                username VARCHAR(255),
                full_name VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')

        # Indekslar (tezlik uchun)
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_conv_user_status ON conversations(user_id, status)')
        await conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_mapping_specialist ON message_mapping(specialist_message_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id)')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_specialists_active ON specialists(is_active)')

    # ✅ .env dan mutaxassislarni avtomatik yuklash
    await _load_specialists_from_env()


async def _load_specialists_from_env():
    """
    .env faylidan mutaxassislarni o'qib database'ga yozish
    """
    categories = ["admin1", "admin2", "admin3", "admin4"]

    for category in categories:
        chat_id_str = os.getenv(f"SPECIALIST_{category.upper()}_CHAT_ID")
        full_name = os.getenv(f"SPECIALIST_{category.upper()}_NAME")
        username = os.getenv(f"SPECIALIST_{category.upper()}_USERNAME")

        # Agar chat_id mavjud bo'lsa, database'ga yozamiz
        if chat_id_str:
            try:
                chat_id = int(chat_id_str)
                await upsert_specialist(category, chat_id, username, full_name)
                print(f"✅ {category}: {full_name or username or chat_id} yuklandi")
            except ValueError:
                print(f"⚠️ {category}: chat_id noto'g'ri ({chat_id_str})")
        else:
            print(f"⚠️ {category}: SPECIALIST_{category.upper()}_CHAT_ID topilmadi")


async def close_db():
    """
    Connection pool'ni yopish (bot to'xtaganda).
    """
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def _require_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool is not initialized. Call await init_db() before using DB functions.")
    return _pool


# --- CRUD operatsiyalar ---

async def save_user(user_id: int, username: str | None, first_name: str | None):
    pool = _require_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id, username, first_name
        )


async def create_conversation(user_id: int, category: str, specialist_chat_id: int) -> int:
    pool = _require_pool()
    async with pool.acquire() as conn:
        conv_id = await conn.fetchval(
            """
            INSERT INTO conversations (user_id, category, specialist_chat_id)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            user_id, category, specialist_chat_id
        )
        return int(conv_id)


async def get_active_conversation(user_id: int):
    pool = _require_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, specialist_chat_id
            FROM conversations
            WHERE user_id = $1 AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
            """,
            user_id
        )
        return (row["id"], row["specialist_chat_id"]) if row else None


async def save_message(conversation_id: int, from_role: str, text: str, telegram_message_id: int):
    pool = _require_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO messages (conversation_id, from_role, message_text, telegram_message_id)
            VALUES ($1, $2, $3, $4)
            """,
            conversation_id, from_role, text, telegram_message_id
        )


async def save_message_mapping(specialist_message_id: int, conversation_id: int, user_message_id: int):
    pool = _require_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO message_mapping (specialist_message_id, conversation_id, user_message_id)
            VALUES ($1, $2, $3)
            """,
            specialist_message_id, conversation_id, user_message_id
        )


async def get_conversation_by_specialist_message(specialist_message_id: int):
    pool = _require_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT conversation_id
            FROM message_mapping
            WHERE specialist_message_id = $1
            """,
            specialist_message_id
        )
        return int(row["conversation_id"]) if row else None


async def get_user_by_conversation(conversation_id: int):
    pool = _require_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id FROM conversations WHERE id = $1",
            conversation_id
        )
        return int(row["user_id"]) if row else None


async def close_conversation(conversation_id: int):
    pool = _require_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE conversations SET status = 'closed' WHERE id = $1",
            conversation_id
        )


async def get_user_phone(user_id: int) -> str | None:
    pool = _require_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT phone FROM users WHERE user_id = $1",
            user_id
        )


async def save_contact(user_id: int, phone: str):
    pool = _require_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, phone)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET phone = EXCLUDED.phone
            """,
            user_id, phone
        )


async def upsert_specialist(category: str, chat_id: int, username: str | None, full_name: str | None):
    pool = _require_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO specialists (category, chat_id, username, full_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (category)
            DO UPDATE SET
                chat_id = EXCLUDED.chat_id,
                username = EXCLUDED.username,
                full_name = EXCLUDED.full_name,
                is_active = TRUE,
                updated_at = NOW()
            """,
            category, chat_id, username, full_name
        )


async def get_specialist_chat_id_by_category(category: str) -> int | None:
    pool = _require_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT chat_id
            FROM specialists
            WHERE category = $1 AND is_active = TRUE
            """,
            category
        )
        return int(row["chat_id"]) if row else None


async def is_specialist(chat_id: int) -> bool:
    pool = _require_pool()
    async with pool.acquire() as conn:
        val = await conn.fetchval(
            """
            SELECT 1
            FROM specialists
            WHERE chat_id = $1 AND is_active = TRUE
            """,
            chat_id
        )
        return val is not None


# ✅ YANGI FUNKSIYALAR - Dinamik keyboard uchun

async def get_all_specialists():
    """
    Barcha ro'yxatdan o'tgan mutaxassislarni qaytaradi
    """
    pool = _require_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT category, chat_id, username, full_name 
            FROM specialists 
            WHERE is_active = TRUE
            ORDER BY category
            """
        )
        return [dict(row) for row in rows]


async def get_specialist_by_full_name(full_name: str):
    """
    Ism-familiya bo'yicha mutaxassisni topadi
    """
    pool = _require_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT category, chat_id, username, full_name 
            FROM specialists 
            WHERE full_name = $1 AND is_active = TRUE
            """,
            full_name
        )
        return dict(row) if row else None