import os
import logging
import asyncpg
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart

# === Настройки окружения ===
API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
DB_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", default=8000))

# === Инициализация ===
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("\ud83d\udce2 \u041a\u0430\u043d\u0430\u043b\u044b"))
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("\ud83c\udfcb \u0421\u043f\u043e\u0440\u0442", url="https://t.me/sportsoda"),
    InlineKeyboardButton("\ud83d\uddde \u041f\u0440\u043e\u0444\u043a\u043e\u043c", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("\ud83d\udcda \u041e\u0422\u0438\u041f\u0411", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("\ud83d\udca1 \u0424\u0430\u0431\u0440\u0438\u043a\u0430 \u0438\u0434\u0435\u0439", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("\ud83e\udde0 \u0427\u0442\u043e \u0442\u0430\u043a\u043e\u0435 \u0411\u0421\u0410", url="https://t.me/your_invest_channel"),
)

# === База данных ===
db_pool = None

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

async def get_all_users():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id FROM users")
        return [row["id"] for row in rows]

# === Команды ===
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await add_user(message.from_user.id)
    caption = "\ud83d\udc4b <b>\u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c!</b>\n\n\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0443 \u043d\u0438\u0436\u0435, \u0447\u0442\u043e\u0431\u044b \u043f\u043e\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c \u043a\u0430\u043d\u0430\u043b\u044b."
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo=photo, caption=caption, reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer(caption, reply_markup=reply_kb)

@dp.message_handler(lambda msg: msg.text == "\ud83d\udce2 \u041a\u0430\u043d\u0430\u043b\u044b")
async def show_channels(message: types.Message):
    await message.answer("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0438\u043d\u0442\u0435\u0440\u0435\u0441\u0443\u044e\u0449\u0438\u0439 \u043a\u0430\u043d\u0430\u043b:", reply_markup=inline_kb)

@dp.message_handler(commands=["list_users"])
async def list_users_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("\u26d4 \u0423 \u0442\u0435\u0431\u044f \u043d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430 \u043a \u044d\u0442\u043e\u0439 \u043a\u043e\u043c\u0430\u043d\u0434\u0435.")
        return

    users = await get_all_users()
    if users:
        user_list = "\n".join(str(uid) for uid in users)
        await message.answer(f"\ud83d\udc65 \u0421\u043f\u0438\u0441\u043e\u043a \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439:\n{user_list}")
    else:
        await message.answer("\u041f\u043e\u043a\u0430 \u0447\u0442\u043e \u043d\u0435\u0442 \u043d\u0438 \u043e\u0434\u043d\u043e\u0433\u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f \u0432 \u0431\u0430\u0437\u0435 \u0434\u0430\u043d\u043d\u044b\u0445.")

# === Рассылка из канала ===
@dp.channel_post_handler()
async def forward_post(message: types.Message):
    await bot.send_message(ADMIN_ID, f"\ud83d\udd0e Получен пост: {message.content_type}")

    users = await get_all_users()
    if not users:
        print("[LOG] Нет пользователей для рассылки.")
        return

    try:
        channel = await bot.get_chat(message.chat.id)
        from_info = f"<b>\ud83d\udce2 \u041a\u0430\u043d\u0430\u043b:</b> <i>{channel.title}</i>\n\n"
    except:
        from_info = ""

    caption = from_info + (message.caption or message.text or "")
    if len(caption) > 1024:
        caption = caption[:1020] + "..."

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
                await bot.send_message(user_id, from_info + "\ud83d\udccc \u041d\u043e\u0432\u044b\u0439 \u043f\u043e\u0441\u0442 \u0432 \u043a\u0430\u043d\u0430\u043b\u0435.")
        except Exception as e:
            await bot.send_message(ADMIN_ID, f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u0434\u043e\u0441\u0442\u0430\u0432\u043a\u0438 \u0434\u043b\u044f {user_id}: {e}")

# === Webhook setup ===
async def on_startup(app):
    global db_pool
    db_pool = await create_pool()
    await bot.set_webhook(WEBHOOK_URL)
    print(f"\ud83d\udce1 Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()

async def handle_webhook(request):
    body = await request.read()
    update = types.Update.de_json(body.decode("utf-8"))
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    await dp.process_update(update)
    return web.Response()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == '__main__':
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)