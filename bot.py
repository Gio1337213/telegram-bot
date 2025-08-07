import os
import logging
from aiohttp import web
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.dispatcher.webhook import get_new_configured_app
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.executor import start_webhook

API_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", default=8000))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

db_pool = None

async def create_pool():
    return await asyncpg.create_pool(dsn=DB_URL)

@dp.message_handler(commands=["start"])
async def start_handler(message: Message):
    user_id = message.from_user.id

    # Сохраняем в PostgreSQL
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY
            )
        """)
        await conn.execute("INSERT INTO users (id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

    await message.answer("Привет! Ты добавлен в базу данных.")
    print(f"Пользователь {user_id} добавлен в базу данных.")

async def on_startup(app):
    global db_pool
    db_pool = await create_pool()
    await bot.set_webhook(WEBHOOK_URL)
    print("Бот запущен и вебхук установлен")

async def on_shutdown(app):
    await bot.delete_webhook()
    await db_pool.close()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH))
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == '__main__':
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
