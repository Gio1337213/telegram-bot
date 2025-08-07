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

# Карта каналов: username -> название
channel_map = {
    "sportsoda": "🏋 ️ Спорт",
    "profkomsoda": "📜 Профком",
    "FabrikaIdeySoda":  "💡 Фабрика идей",
    "LINK":  "📚 ОТиПБ"
}

# Клавиатура с двумя кнопками
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("📢 Каналы"),
    KeyboardButton("🔔 Подписки")
)

# Кнопки со ссылками на каналы
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("🏋 ️ Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("📜 Профком", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("📚 ОТиПБ", url="https://t.me/FabrikaIdeySoda"),
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
            );
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                user_id BIGINT,
                channel_name TEXT,
                PRIMARY KEY (user_id, channel_name),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        await conn.execute("INSERT INTO users (id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

async def get_users():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id FROM users")
        return [row["id"] for row in rows]

# Хендлер /start
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await add_user(message.from_user.id)
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo, caption="👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы.", reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer("👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы.", reply_markup=reply_kb)

# Кнопка "📢 Каналы"
@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def channels(message: types.Message):
    await message.answer("Выберите интересующий канал:", reply_markup=inline_kb)

# Кнопка "🔔 Подписки"
@dp.message_handler(lambda msg: msg.text == "🔔 Подписки")
async def manage_subscriptions(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    for channel, title in channel_map.items():
        kb.add(InlineKeyboardButton(f"{title}", callback_data=f"toggle_sub:{channel}"))
    await message.answer("Выберите темы для получения уведомлений:", reply_markup=kb)

# Обработка нажатия на кнопку подписки/отписки
@dp.callback_query_handler(lambda c: c.data.startswith("toggle_sub:"))
async def toggle_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    channel = callback.data.split(":")[1]

    async with db_pool.acquire() as conn:
        subscribed = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM user_subscriptions WHERE user_id=$1 AND channel_name=$2
            )
        """, user_id, channel)

        if subscribed:
            await conn.execute("""
                DELETE FROM user_subscriptions WHERE user_id=$1 AND channel_name=$2
            """, user_id, channel)
            await callback.answer("❌ Отписка от канала", show_alert=False)
            await bot.send_message(user_id, f"❌ Вы отписались от рассылки: <b>{channel_map.get(channel, channel)}</b>")
        else:
            await conn.execute("""
                INSERT INTO user_subscriptions (user_id, channel_name)
                VALUES ($1, $2) ON CONFLICT DO NOTHING
            """, user_id, channel)
            await callback.answer("✅ Подписка оформлена", show_alert=False)
            await bot.send_message(user_id, f"✅ Вы подписались на рассылку: <b>{channel_map.get(channel, channel)}</b>")

# Обработка постов из канала (включая медиа)
@dp.channel_post_handler(content_types=types.ContentType.ANY)
async def forward_post(message: types.Message):
    caption = message.caption or message.text or ""
    clean_caption = re.sub(r'@\w+', '', caption).strip()

    try:
        channel = await bot.get_chat(message.chat.id)
        channel_name = channel.username
        if channel_name in channel_map:
            title = channel_map[channel_name]
            post_link = f"https://t.me/{channel_name}/{message.message_id}"
            from_info = f'<b>📢 <a href="{post_link}">{title}</a></b>\n\n'
        else:
            return  # канал не в списке — пропустить
    except:
        return

    full_caption = from_info + clean_caption
    if len(full_caption) > 1024:
        full_caption = full_caption[:1020] + "..."

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT user_id FROM user_subscriptions WHERE channel_name=$1
        """, channel_name)
        user_ids = [r["user_id"] for r in rows]

    for uid in user_ids:
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

# Webhook
async def on_startup(dp):
    global db_pool
    db_pool = await create_pool()
    await bot.set_webhook(
        WEBHOOK_URL,
        allowed_updates=["message", "callback_query"]
    )

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
