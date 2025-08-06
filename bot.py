import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.webhook import get_new_configured_app
from aiogram.dispatcher.filters import CommandStart
from aiohttp import web

API_TOKEN = os.getenv("API_TOKEN")  # Убедись, что переменная задана в Render!
WEBHOOK_HOST = "https://telegram-bot-fa47.onrender.com"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_PORT = int(os.getenv("PORT", default=10000))
USERS_FILE = "users.json"

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Клавиатуры
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("📢 Каналы"))
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("🏋 Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("📰 Профком", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("📚 ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("💡 Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("🧠 Что такое БСА", url="https://t.me/your_invest_channel"),
)

# Загрузка пользователей
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
        print(f"[LOG] Добавлен пользователь: {user_id}")

# /start
@dp.message_handler(CommandStart())
async def start(message: types.Message):
    save_user(message.from_user.id)
    caption = "👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы."
    try:
        with open("welcome.jpg", "rb") as photo:
            await message.answer_photo(photo=photo, caption=caption, reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer(caption, reply_markup=reply_kb)

# Каналы
@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def show_channels(message: types.Message):
    await message.answer("Выберите интересующий канал:", reply_markup=inline_kb)

# Пересылка из канала
@dp.channel_post_handler()
async def handle_channel_post(msg: types.Message):
    print(f"[LOG] Новый пост: {msg.content_type}")
    if msg.photo:
        await bot.send_photo(6050553187, msg.photo[-1].file_id, caption=msg.caption or "Фото без подписи")
    elif msg.text:
        await bot.send_message(6050553187, msg.text)
    else:
        await bot.send_message(6050553187, "Тип сообщения не поддержан")

# Webhook
async def on_startup(app):
    print(f"[LOG] 📡 Устанавливаю Webhook на: {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()

app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=WEBAPP_PORT)
