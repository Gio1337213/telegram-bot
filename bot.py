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
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS media (
                id SERIAL PRIMARY KEY,
                file_id TEXT NOT NULL,
                type TEXT NOT NULL,
                caption TEXT
            )
        """)
        await conn.execute("INSERT INTO users (id) VALUES ($1) ON CONFLICT DO NOTHING", user_id)

async def get_all_users():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id FROM users")
        return [row["id"] for row in rows]

async def save_media(file_id: str, media_type: str, caption: str = None):
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO media (file_id, type, caption) VALUES ($1, $2, $3)",
            file_id, media_type, caption
        )

async def send_saved_media_to_all_users():
    users = await get_all_users()
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT file_id, type, caption FROM media")

    for row in rows:
        for user_id in users:
            try:
                if row["type"] == "photo":
                    await bot.send_photo(user_id, row["file_id"], caption=row["caption"])
                elif row["type"] == "video":
                    await bot.send_video(user_id, row["file_id"], caption=row["caption"])
                elif row["type"] == "document":
                    await bot.send_document(user_id, row["file_id"], caption=row["caption"])
                elif row["type"] == "text":
                    await bot.send_message(user_id, row["file_id"])
            except Exception as e:
                await bot.send_message(ADMIN_ID, f"⚠️ Ошибка отправки {user_id}: {e}")

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

@dp.message_handler(commands=["broadcast"], user_id=ADMIN_ID)
async def broadcast_media(message: types.Message):
    await message.answer("🚀 Рассылка началась...")
    await send_saved_media_to_all_users()
    await message.answer("✅ Рассылка завершена.")

@dp.message_handler(commands=["clear_media"], user_id=ADMIN_ID)
async def clear_media(message: types.Message):
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM media")
    await message.answer("🗑 Все сохранённые медиа удалены.")

@dp.message_handler(lambda msg: msg.from_user.id == ADMIN_ID, content_types=types.ContentType.ANY)
async def handle_admin_media(message: types.Message):
    if message.photo:
        file_id = message.photo[-1].file_id
        await save_media(file_id, "photo", message.caption)
        await message.reply("✅ Фото сохранено в базу.")
    elif message.video:
        file_id = message.video.file_id
        await save_media(file_id, "video", message.caption)
        await message.reply("✅ Видео сохранено в базу.")
    elif message.document:
        file_id = message.document.file_id
        await save_media(file_id, "document", message.caption)
        await message.reply("✅ Документ сохранён в базу.")
    elif message.text:
        await save_media(message.text, "text")
        await message.reply("✅ Текст сохранён в базу.")
    else:
        await message.reply("⚠️ Тип медиа не поддерживается.")

# === Обработка постов из канала ===
@dp.channel_post_handler()
async def forward_post(message: types.Message):
    await bot.send_message(ADMIN_ID, f"🧪 [DEBUG] Получено обновление.\n"
                                     f"Тип: {message.content_type}\n"
                                     f"ID канала: {message.chat.id}\n"
                                     f"Текст: {message.text or message.caption or 'нет'}")
    users = await get_all_users()
    if not users:
        await bot.send_message(ADMIN_ID, "❌ Нет пользователей для рассылки.")
        return

    try:
        channel = await bot.get_chat(message.chat.id)
        from_info = f"<b>📢 Канал:</b> <i>{channel.title}</i>\n\n"
    except:
        from_info = ""

    caption = from_info + (message.caption or message.text or "")
    if len(caption) > 1024:
        caption = caption[:1020] + "..."

    await bot.send_message(
        ADMIN_ID,
        f"📨 Получен пост из канала: {message.chat.title}\n"
        f"👥 Отправляется {len(users)} пользователям.\n"
        f"📎 Тип: {'photo' if message.photo else 'video' if message.video else 'text'}"
    )

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
            await bot.send_message(ADMIN_ID, f"⚠️ Ошибка отправки {user_id}: {e}")

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
