import os
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.webhook import get_new_configured_app
from aiohttp import web
from aiohttp import ClientSession
import asyncpg

# === Настройки ===
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://telegram-bot-fa47.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", default=10000))
DB_URL = os.getenv("postgresql://telegram_bot_db_1nn8_user:Xu7cM4HqwLSlb60RzmScQSz6eCzRSHKG@dpg-d2a5bp15pdvs73ad634g-a/telegram_bot_db_1nn8")  # URL PostgreSQL от Render

logging.basicConfig(level=logging.INFO)

# === Инициализация ===
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
db_pool = None  # создаём позже в on_startup

# === Интерфейс ===
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📢 Каналы"))
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("🏋 Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("📰 Профком", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("📚 ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("💡 Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("🧠 Что такое БСА", url="https://t.me/your_invest_channel"),
)

# === Работа с пользователями через PostgreSQL ===
async def create_pool():
    return await asyncpg.create_pool(dsn=DB_URL)

async def add_user(user_id):
    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO users (id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

async def get_all_users():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id FROM users")
        return [row["id"] for row in rows]

# === Старт ===
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await add_user(message.from_user.id)
    caption = "👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы."
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo=photo, caption=caption, reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer(caption, reply_markup=reply_kb)

@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def show_channels(message: types.Message):
    await message.answer("Выберите интересующий канал:", reply_markup=inline_kb)

# === Рассылка постов из канала ===
@dp.channel_post_handler()
async def forward_post(message: types.Message):
    users = await get_all_users()
    if not users:
        print("[LOG] Нет пользователей для рассылки.")
        return

    try:
        channel = await bot.get_chat(message.chat.id)
        from_info = f"<b>📢 Канал:</b> <i>{channel.title}</i>\n\n"
    except:
        from_info = ""

    caption = from_info + (message.caption or message.text or "")
    if len(caption) > 1024:
        caption = caption[:1020] + "..."

    print(f"[LOG] Получен пост из канала: {channel.title if 'channel' in locals() else message.chat.id}")
    print(f"[LOG] Рассылка {len(users)} пользователям...")

    for user_id in users:
        try:
            if message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id, caption=caption)
            elif message.video:
                await bot.send_video(user_id, message.video.file_id, caption=caption)
            elif message.document:
                await bot.send_document(user_id, message.document.file_id, caption=caption)
            elif message.animation:
                await bot.send_animation(user_id, message.animation.file_id, caption=caption)
            elif message.text:
                await bot.send_message(user_id, caption)
            else:
                await bot.send_message(user_id, from_info + "📌 Новый пост в канале.")
        except Exception as e:
            print(f"❌ Ошибка отправки {user_id}: {e}")

# === Вебхук ===
async def on_startup(app):
    global db_pool
    db_pool = await create_pool()
    logging.info(f"📡 Устанавливаю Webhook: {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()

app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
