import os
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.webhook import get_new_configured_app
from aiohttp import web
from aiohttp import ClientSession
from pathlib import Path

# === Настройка ===
API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://telegram-bot-fa47.onrender.com")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", default=10000))
USERS_FILE = "users.json"
MEDIA_DIR = "media"

logging.basicConfig(level=logging.INFO)

# === Инициализация ===
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# === Интерфейс ===
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📢 Каналы"))
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("🏋 Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("📰 Профком", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("📚 ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("💡 Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("🧠 Что такое БСА", url="https://t.me/your_invest_channel"),
)

# === Работа с пользователями ===
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

# === Старт ===
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    save_user(message.from_user.id)
    caption = "👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы."
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo=photo, caption=caption, reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer(caption, reply_markup=reply_kb)

@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def show_channels(message: types.Message):
    await message.answer("Выберите интересующий канал:", reply_markup=inline_kb)

# === Рассылка постов из канала (с загрузкой медиа) ===
@dp.channel_post_handler()
async def forward_post(message: types.Message):
    users = load_users()
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
