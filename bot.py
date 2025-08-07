import os
import logging
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart
from aiogram.utils.executor import start_webhook

# === Логирование ===
logging.basicConfig(level=logging.INFO)

# === Настройки окружения ===
API_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
DB_URL = os.getenv("DATABASE_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", default=8000))

# === Инициализация бота ===
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📢 Каналы"))
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("🏋 Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("📰 Профком", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("📚 ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("💡 Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("🧠 Что такое БСА", url="https://t.me/your_invest_channel"),
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
    caption = "👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы."
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo=photo, caption=caption, reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer(caption, reply_markup=reply_kb)

@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def show_channels(message: types.Message):
    await message.answer("Выберите интересующий канал:", reply_markup=inline_kb)

@dp.message_handler(commands=["list_users"])
async def list_users_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа к этой команде.")
        return

    users = await get_all_users()
    if users:
        user_list = "\n".join(str(uid) for uid in users)
        await message.answer(f"👥 Список пользователей:\n{user_list}")
    else:
        await message.answer("Пока что нет ни одного пользователя в базе данных.")

# === Обработка постов из канала ===
@dp.channel_post_handler()
async def forward_post(message: types.Message):
    users = await get_all_users()
    if not users:
        logging.info("[LOG] Нет пользователей для рассылки.")
        return

    try:
        channel = await bot.get_chat(message.chat.id)
        from_info = f"<b>📢 Канал:</b> <i>{channel.title}</i>\n\n"
    except:
        from_info = ""

    caption = from_info + (message.caption or message.text or "")
    if len(caption) > 1024:
        caption = caption[:1020] + "..."

    logging.info(f"[LOG] Рассылка {len(users)} пользователям...")

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
            logging.warning(f"❌ Ошибка отправки {user_id}: {e}")

# === Webhook запуск ===
async def on_startup(dp):
    global db_pool
    db_pool = await create_pool()
    logging.info(f"📡 Устанавливаю Webhook: {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    logging.info("🔌 Отключаю webhook и сессию...")
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