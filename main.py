import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import init_db, close_db
from handlers import start, user_messages, specialist_replies

logging.basicConfig(level=logging.INFO)


async def main():
    # async DB init
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(start.router)
    dp.include_router(specialist_replies.router)
    dp.include_router(user_messages.router)

    logging.info("✅ Bot ishga tushdi (PostgreSQL + asyncpg)")

    try:
        await dp.start_polling(bot)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())