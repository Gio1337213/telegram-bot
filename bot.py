import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.executor import start_webhook

API_TOKEN = os.getenv("API_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # Например: https://your-bot.onrender.com
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 3000))

USERS_FILE = "users.json"
PHOTO_PATH = "welcome.jpg"

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Загрузка пользователей
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

# Сохранение нового пользователя
def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

# Реплай-клавиатура
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reply_kb.add(KeyboardButton("📢 Каналы"))

# Инлайн-кнопки каналов
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("🏋 Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("📰 Профком", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("📚 ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("💡 Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("🧠 Что такое БСА", url="https://t.me/your_invest_channel"),
)

# /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    save_user(message.from_user.id)
    caption = "👋 <b>Добро пожаловать!</b>\n\nНажмите кнопку ниже, чтобы посмотреть каналы."
    if os.path.exists(PHOTO_PATH):
        with open(PHOTO_PATH, 'rb') as photo:
            await message.answer_photo(photo, caption=caption, reply_markup=reply_kb)
    else:
        await message.answer(caption, reply_markup=reply_kb)

# Кнопка "Каналы"
@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def show_channels(msg: types.Message):
    await msg.answer("Выберите интересующий канал:", reply_markup=inline_kb)

# Пересылка постов из канала
@dp.channel_post_handler()
async def forward_to_users(post: types.Message):
    users = load_users()

    # Получаем название канала
    try:
        channel = await bot.get_chat(post.chat.id)
        prefix = f"<b>📢 Канал:</b> <i>{channel.title}</i>\n\n"
    except:
        prefix = ""

    for user_id in users:
        try:
            if post.text:
                await bot.send_message(user_id, prefix + post.text)
            elif post.caption and post.photo:
                await bot.send_photo(user_id, post.photo[-1].file_id, caption=prefix + post.caption)
            elif post.caption and post.video:
                await bot.send_video(user_id, post.video.file_id, caption=prefix + post.caption)
            elif post.caption and post.document:
                await bot.send_document(user_id, post.document.file_id, caption=prefix + post.caption)
            elif post.caption and post.animation:
                await bot.send_animation(user_id, post.animation.file_id, caption=prefix + post.caption)
        except Exception as e:
            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")

# === Webhook Startup & Shutdown ===

async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dispatcher):
    await bot.delete_webhook()

# === Запуск ===

if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
