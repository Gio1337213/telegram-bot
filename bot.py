import os
import logging
import asyncpg
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook

# === Настройки ===
API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # Пример: https://your-app.onrender.com
DB_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
db_pool = None

# === Клавиатуры ===
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📢 Каналы"))
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("🏋 ️ Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("📜 Профком", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("📚 ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("💡 Фабрика идей", url="https://t.me/your_invest_channel")
)

# === База данных ===
async def create_pool():
    return await asyncpg.create_pool(dsn=DB_URL)

async def add_user(user_id):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY
            )
        """)
        await conn.execute("INSERT INTO users (id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

async def get_users():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id FROM users")
        return [row["id"] for row in rows]

# === Хендлеры ===
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await add_user(message.from_user.id)
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo, caption="👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы.", reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer("\ud83d\udc4b <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы.", reply_markup=reply_kb)

@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def channels(message: types.Message):
    await message.answer("Выберите интересующий канал:", reply_markup=inline_kb)

# Рассылка постов
@dp.channel_post_handler()
async def debug_channel_post(message: types.Message):
    try:
        await bot.send_message(ADMIN_ID, f"📥 Получен пост из канала.\n"
                                         f"ID: <code>{message.message_id}</code>\n"
                                         f"Тип: {'Фото' if message.photo else 'Нет фото'}")

        if message.photo:
            await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption="✅ Фото получено через webhook")
        elif message.text:
            await bot.send_message(ADMIN_ID, f"Текст: {message.text}")
        else:
            await bot.send_message(ADMIN_ID, "❓ Неизвестный формат сообщения")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"❌ Ошибка в debug handler: {e}")


# === Webhook ===
async def on_startup(dp):
    global db_pool
    db_pool = await create_pool()
    await bot.set_webhook(WEBHOOK_URL)
    await bot.send_message(ADMIN_ID, f"Webhook активен: {WEBHOOK_URL}")

async def on_shutdown(dp):
    await bot.delete_webhook()
    await bot.session.close()

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )