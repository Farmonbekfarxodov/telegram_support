# config.py
import os
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "support_bot")

# Mutaxassislar (endi database'dan olinadi)
SPECIALISTS = {
    "admin1": {
        "name": "👤 Admin 1",
        "chat_id": int(os.getenv("SPECIALIST_ADMIN1_CHAT_ID", "0")) if os.getenv("SPECIALIST_ADMIN1_CHAT_ID") else None,
        "username": "@admin1"
    },
    "admin2": {
        "name": "👤 Admin 2",
        "chat_id": int(os.getenv("SPECIALIST_ADMIN2_CHAT_ID", "0")) if os.getenv("SPECIALIST_ADMIN2_CHAT_ID") else None,
        "username": "@admin2"
    },
    "admin3": {
        "name": "👤 Admin 3",
        "chat_id": int(os.getenv("SPECIALIST_ADMIN3_CHAT_ID", "0")) if os.getenv("SPECIALIST_ADMIN3_CHAT_ID") else None,
        "username": "@admin3"
    },
    "admin4": {
        "name": "👤 Admin 4",
        "chat_id": int(os.getenv("SPECIALIST_ADMIN4_CHAT_ID", "0")) if os.getenv("SPECIALIST_ADMIN4_CHAT_ID") else None,
        "username": "@admin4"
    }
}

# Xavfsizlik tekshiruvi
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN .env faylida topilmadi!")
if not DB_PASSWORD:
    raise ValueError("❌ DB_PASSWORD .env faylida topilmadi!")

print("✅ Config yuklandi:")
print(f"  - Bot token: {'✓' if BOT_TOKEN else '✗'}")
print(f"  - Database: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
print(f"  - Mutaxassislar: {len([s for s in SPECIALISTS.values() if s['chat_id']])} ta tayyor")