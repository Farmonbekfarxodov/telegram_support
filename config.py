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

# Mutaxassislar (chat_id .env dan yoki keyinchalik qo'lda to'ldiriladi)
SPECIALISTS = {
    "texnik": {
        "name": "📞 Texnik Yordam",
        "chat_id": int(os.getenv("SPECIALIST_TEXNIK_CHAT_ID", "0")) if os.getenv("SPECIALIST_TEXNIK_CHAT_ID") else None,
        "username": "@nickname1"
    },
    "savdo": {
        "name": "💼 Savdo Bo'limi",
        "chat_id": int(os.getenv("SPECIALIST_SAVDO_CHAT_ID", "0")) if os.getenv("SPECIALIST_SAVDO_CHAT_ID") else None,
        "username": "@nickname2"
    },
    "konsultatsiya": {
        "name": "📊 Konsultatsiya",
        "chat_id": int(os.getenv("SPECIALIST_KONSULTATSIYA_CHAT_ID", "0")) if os.getenv("SPECIALIST_KONSULTATSIYA_CHAT_ID") else None,
        "username": "@nickname3"
    },
    "boshqa": {
        "name": "⚙️ Boshqa",
        "chat_id": int(os.getenv("SPECIALIST_BOSHQA_CHAT_ID", "0")) if os.getenv("SPECIALIST_BOSHQA_CHAT_ID") else None,
        "username": "@nickname4"
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