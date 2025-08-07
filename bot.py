import os
import asyncpg
import re
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook

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

# Клавиатуры
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📢 Каналы"))
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("🏋 ️ Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("📜 Профком", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("📚 ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("💡 Фабрика идей", url="https://t.me/your_invest_channel")
)

# База данных
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

# Хендлеры
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await add_user(message.from_user.id)
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo, caption="👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы.", reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer("👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы.", reply_markup=reply_kb)

@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def channels(message: types.Message):
    await message.answer("Выберите интересующий канал:", reply_markup=inline_kb)

# Обработка постов из канала (включая медиа)
@dp.channel_post_handler(content_types=types.ContentType.ANY)
async def forward_post(message: types.Message):
    caption = message.caption or message.text or ""
    
    # Очистка caption от ссылок на Telegram и упоминаний
    clean_caption = re.sub(r'https?://t\.me/\S+', '', caption)
    clean_caption = re.sub(r'@\w+', '', clean_caption)

    try:
        channel = await bot.get_chat(message.chat.id)
        if channel.username:
            post_link = f"https://t.me/{channel.username}/{message.message_id}"
            from_info = f'<b>📢 <a href="{post_link}">{channel.title}</a></b>\n\n'
        else:
            from_info = f"<b>📢 Канал:</b> <i>{channel.title}</i>\n\n"
    except:
        from_info = ""

    full_caption = from_info + clean_caption.strip()
    if len(full_caption) > 1024:
        full_caption = full_caption[:1020] + "..."

    users = await get_users()

    for uid in users:
        try:
            if message.photo:
                await bot.send_photo(uid, message.photo[-1].file_id, caption=full_caption, disable_web_page_preview=True)
            elif message.video:
                await bot.send_video(uid, message.video.file_id, caption=full_caption, disable_web_page_preview=True)
            elif message.document:
                await bot.send_document(uid, message.document.file_id, caption=full_caption, disable_web_page_preview=True)
            elif message.animation:
                await bot.send_animation(uid, message.animation.file_id, caption=full_caption, disable_web_page_preview=True)
            elif message.text:
                await bot.send_message(uid, full_caption, disable_web_page_preview=True)
            else:
                await bot.send_message(uid, from_info + "📌 Новый пост в канале.", disable_web_page_preview=True)
        except:
            pass  # опционально: логировать ошибку для uid

# Webhook
async def on_startup(dp):
    global db_pool
    db_pool = await create_pool()
    await bot.set_webhook(WEBHOOK_URL)

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
