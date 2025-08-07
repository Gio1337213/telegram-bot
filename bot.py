import os
import asyncpg
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.executor import start_webhook

API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
DB_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
db_pool = None

reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("\ud83d\udce2 Каналы"))

channels = {
    "sport": ("\ud83c\udfcb Спорт", "https://t.me/sportsoda"),
    "profkom": ("\ud83d\udcdc Профком", "https://t.me/profkomsoda"),
    "ideas": ("\ud83d\udca1 Фабрика идей", "http"),
    "safety": ("\ud83d\udcda ОТиПБ", "http")
}

def subscription_keyboard(user_subs):
    buttons = []
    for key, (name, _) in channels.items():
        mark = "✅" if key in user_subs else "❌"
        buttons.append([InlineKeyboardButton(f"{name} {mark}", callback_data=f"toggle:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# DB
async def create_pool():
    return await asyncpg.create_pool(dsn=DB_URL)

async def add_user(user_id):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (id BIGINT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id BIGINT,
                channel_key TEXT,
                PRIMARY KEY (user_id, channel_key)
            );
        """)
        await conn.execute("INSERT INTO users (id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

async def get_users():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id FROM users")
        return [row["id"] for row in rows]

async def get_user_subs(user_id):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT channel_key FROM subscriptions WHERE user_id = $1", user_id)
        return [row["channel_key"] for row in rows]

async def get_channel_subscribers(channel_key):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM subscriptions WHERE channel_key = $1", channel_key)
        return [row["user_id"] for row in rows]

# Хендлеры
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await add_user(message.from_user.id)
    subs = await get_user_subs(message.from_user.id)
    await message.answer("Выберите интересующие каналы:", reply_markup=subscription_keyboard(subs))

@dp.message_handler(lambda msg: msg.text == "\ud83d\udce2 Каналы")
async def channels_list(message: types.Message):
    subs = await get_user_subs(message.from_user.id)
    await message.answer("Вы можете подписаться или отписаться от каналов:", reply_markup=subscription_keyboard(subs))

@dp.callback_query_handler(lambda c: c.data.startswith("toggle:"))
async def toggle_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    key = callback.data.split(":")[1]
    async with db_pool.acquire() as conn:
        exists = await conn.fetchval("SELECT 1 FROM subscriptions WHERE user_id=$1 AND channel_key=$2", user_id, key)
        if exists:
            await conn.execute("DELETE FROM subscriptions WHERE user_id=$1 AND channel_key=$2", user_id, key)
        else:
            await conn.execute("INSERT INTO subscriptions (user_id, channel_key) VALUES ($1, $2)", user_id, key)
        rows = await conn.fetch("SELECT channel_key FROM subscriptions WHERE user_id=$1", user_id)
        subs = [r['channel_key'] for r in rows]
    await callback.message.edit_reply_markup(reply_markup=subscription_keyboard(subs))
    await callback.answer("Обновлено ✅")

@dp.channel_post_handler(content_types=types.ContentType.ANY)
async def forward_post(message: types.Message):
    # Определи канал по username или chat_id:
    channel_key = None
    if message.chat.username == "profkomsoda":
        channel_key = "profkom"
    elif message.chat.username == "sportsoda":
        channel_key = "sport"
    # и т.д.

    if not channel_key:
        return

    caption = message.caption or message.text or ""
    full_caption = f"<b>\ud83d\udce2 <a href='https://t.me/{message.chat.username}/{message.message_id}'>{message.chat.title}</a></b>\n\n" + caption
    if len(full_caption) > 1024:
        full_caption = full_caption[:1020] + "..."

    users = await get_channel_subscribers(channel_key)
    for uid in users:
        try:
            if message.photo:
                await bot.send_photo(uid, message.photo[-1].file_id, caption=full_caption)
            elif message.video:
                await bot.send_video(uid, message.video.file_id, caption=full_caption)
            elif message.animation:
                await bot.send_animation(uid, message.animation.file_id, caption=full_caption)
            elif message.document:
                await bot.send_document(uid, message.document.file_id, caption=full_caption)
            elif message.text:
                await bot.send_message(uid, full_caption, disable_web_page_preview=True)
        except:
            continue

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
