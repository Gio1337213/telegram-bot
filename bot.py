import os
import asyncpg
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

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

# === Reply Keyboard ===
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("\ud83d\udce2 \u041a\u0430\u043d\u0430\u043b\u044b"))
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("\ud83c\udfcb\ufe0f\ufe0f \u0421\u043f\u043e\u0440\u0442", url="https://t.me/sportsoda"),
    InlineKeyboardButton("\ud83d\udcdc \u041f\u0440\u043e\u0444\u043a\u043e\u043c", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("\ud83d\udcda \u041e\u0422\u0438\u041f\u0411", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("\ud83d\udca1 \u0424\u0430\u0431\u0440\u0438\u043a\u0430 \u0438\u0434\u0435\u0439", url="https://t.me/your_invest_channel")
)

# === Database ===
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

# === Handlers ===
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await add_user(message.from_user.id)
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo, caption="\ud83d\udc4b <b>\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c!</b>\n\n\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u043d\u0438\u0436\u0435, \u0447\u0442\u043e\u0431\u044b \u043f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u043a\u0430\u043d\u0430\u043b\u044b.", reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer("\ud83d\udc4b <b>\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c!</b>\n\n\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u043d\u0438\u0436\u0435, \u0447\u0442\u043e\u0431\u044b \u043f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u043a\u0430\u043d\u0430\u043b\u044b.", reply_markup=reply_kb)

@dp.message_handler(lambda msg: msg.text == "\ud83d\udce2 \u041a\u0430\u043d\u0430\u043b\u044b")
async def channels(message: types.Message):
    await message.answer("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0438\u043d\u0442\u0435\u0440\u0435\u0441\u0443\u044e\u0449\u0438\u0439 \u043a\u0430\u043d\u0430\u043b:", reply_markup=inline_kb)

# === Channel post forward ===
@dp.channel_post_handler(content_types=types.ContentType.ANY)
async def forward_post(message: types.Message):
    caption = message.caption or message.text or ""
    try:
        channel = await bot.get_chat(message.chat.id)
        if channel.username:
            post_link = f"https://t.me/{channel.username}/{message.message_id}"
            from_info = f'<b>\ud83d\udce2 <a href="{post_link}">{channel.title}</a></b>\n\n'
        else:
            from_info = f"<b>\ud83d\udce2 \u041a\u0430\u043d\u0430\u043b:</b> <i>{channel.title}</i>\n\n"
    except:
        from_info = ""

    full_caption = from_info + caption
    if len(full_caption) > 1024:
        full_caption = full_caption[:1020] + "..."

    users = await get_users()

    for uid in users:
        try:
            if message.photo:
                await bot.send_photo(uid, message.photo[-1].file_id, caption=full_caption, disable_web_page_preview=True)
            elif message.video:
                await bot.send_video(uid, message.video.file_id, caption=full_caption)
            elif message.document:
                await bot.send_document(uid, message.document.file_id, caption=full_caption)
            elif message.animation:
                await bot.send_animation(uid, message.animation.file_id, caption=full_caption)
            elif message.text:
                await bot.send_message(uid, full_caption, disable_web_page_preview=True)
            else:
                await bot.send_message(uid, from_info + "\ud83d\udccc \u041d\u043e\u0432\u044b\u0439 \u043f\u043e\u0441\u0442 \u0432 \u043a\u0430\u043d\u0430\u043b\u0435.", disable_web_page_preview=True)
        except:
            pass

# === Webhook ===
async def on_startup(app):
    global db_pool
    db_pool = await create_pool()
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == '__main__':
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
