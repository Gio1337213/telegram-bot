import os
import asyncpg
import re
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
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

channels_data = {
    "sportsoda": "🏋️ Спорт",
    "profkomsoda": "📜 Профком",
    "your_invest_channel": "📚 ОТиПБ",
    "ideas_factory": "💡 Фабрика идей"
}

reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📢 Каналы"))

async def create_pool():
    pool = await asyncpg.create_pool(dsn=DB_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                user_id BIGINT,
                channel_username TEXT,
                PRIMARY KEY (user_id, channel_username)
            )
        """)
    return pool

async def add_user(user_id):
    async with db_pool.acquire() as conn:
        await conn.execute("INSERT INTO users (id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

async def get_user_subscriptions(user_id):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT channel_username FROM user_subscriptions WHERE user_id = $1", user_id)
        return [row["channel_username"] for row in rows]

async def get_users_by_channel(channel_username):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT user_id FROM user_subscriptions WHERE channel_username = $1", channel_username)
        return [row["user_id"] for row in rows]

def get_subscription_kb(user_subs):
    kb = InlineKeyboardMarkup(row_width=2)
    for username, title in channels_data.items():
        subscribed = username in user_subs
        sub_action = "unsubscribe" if subscribed else "subscribe"
        sub_label = "✅ Отписаться" if subscribed else "📥 Подписаться"
        kb.add(
            InlineKeyboardButton(sub_label, callback_data=f"{sub_action}:{username}"),
            InlineKeyboardButton("🔗 Канал", url=f"https://t.me/{username}")
        )
    return kb

@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await add_user(message.from_user.id)
    subs = await get_user_subscriptions(message.from_user.id)
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo, caption="👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы выбрать каналы для подписки.", reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer("👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы выбрать каналы для подписки.", reply_markup=reply_kb)

@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def channels(message: types.Message):
    user_subs = await get_user_subscriptions(message.from_user.id)
    await message.answer("Выберите каналы для подписки или отписки:", reply_markup=get_subscription_kb(user_subs))

@dp.callback_query_handler(lambda c: c.data.startswith("subscribe:") or c.data.startswith("unsubscribe:"))
async def handle_subscription(callback_query: types.CallbackQuery):
    action, channel_username = callback_query.data.split(":")
    user_id = callback_query.from_user.id
    async with db_pool.acquire() as conn:
        if action == "subscribe":
            await conn.execute("""
                INSERT INTO user_subscriptions (user_id, channel_username)
                VALUES ($1, $2) ON CONFLICT DO NOTHING
            """, user_id, channel_username)
            await callback_query.answer("Подписка оформлена!")
        elif action == "unsubscribe":
            await conn.execute("DELETE FROM user_subscriptions WHERE user_id = $1 AND channel_username = $2", user_id, channel_username)
            await callback_query.answer("Вы отписались!")

    user_subs = await get_user_subscriptions(user_id)
    await callback_query.message.edit_reply_markup(reply_markup=get_subscription_kb(user_subs))

@dp.channel_post_handler(content_types=types.ContentType.ANY)
async def forward_post(message: types.Message):
    caption = message.caption or message.text or ""
    clean_caption = re.sub(r'@\w+', '', caption).strip()

    try:
        channel = await bot.get_chat(message.chat.id)
        if not channel.username:
            return

        post_link = f"https://t.me/{channel.username}/{message.message_id}"
        from_info = f'<b>📢 <a href="{post_link}">{channel.title}</a></b>\n\n'
        full_caption = from_info + clean_caption
        if len(full_caption) > 1024:
            full_caption = full_caption[:1020] + "..."

        users = await get_users_by_channel(channel.username)

        for uid in users:
            try:
                if message.photo:
                    await bot.send_photo(uid, message.photo[-1].file_id, caption=full_caption)
                elif message.video:
                    await bot.send_video(uid, message.video.file_id, caption=full_caption)
                elif message.document:
                    await bot.send_document(uid, message.document.file_id, caption=full_caption)
                elif message.animation:
                    await bot.send_animation(uid, message.animation.file_id, caption=full_caption)
                elif message.text:
                    await bot.send_message(uid, full_caption, disable_web_page_preview=True)
                else:
                    await bot.send_message(uid, from_info + "📌 Новый пост в канале.", disable_web_page_preview=True)
            except:
                pass
    except:
        pass

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
