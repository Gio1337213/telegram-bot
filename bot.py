 import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart

API_TOKEN = os.getenv("API_TOKEN")
USERS_FILE = "users.json"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Реплай-клавиатура
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reply_kb.add(KeyboardButton("📢 Каналы"))

# Инлайн-кнопки
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("Новости Профкома", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("Что такое БСА", url="https://t.me/your_invest_channel")
)

# Убедись, что файл users.json существует
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# Команда /start
@dp.message_handler(CommandStart())
async def send_welcome(message: types.Message):
    # Добавляем пользователя в users.json
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    if message.from_user.id not in users:
        users.append(message.from_user.id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

    # Приветствие
    caption = "👋 Добро пожаловать!\n\nНажмите кнопку ниже, чтобы выбрать канал:"
    await message.answer(caption, reply_markup=reply_kb)

# Обработка кнопки "Каналы"
@dp.message_handler(lambda message: message.text == "📢 Каналы")
async def show_channels(message: types.Message):
    await message.answer("Выберите канал:", reply_markup=inline_kb)

# РАССЫЛКА из канала — бот должен быть админом!
@dp.channel_post_handler()
async def forward_channel_post(message: types.Message):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    for user_id in users:
        try:
            if message.content_type == "photo":
                await bot.send_photo(chat_id=user_id, photo=message.photo[-1].file_id, caption=message.caption or "")
            elif message.content_type == "video":
                await bot.send_video(chat_id=user_id, video=message.video.file_id, caption=message.caption or "")
            elif message.content_type == "document":
                await bot.send_document(chat_id=user_id, document=message.document.file_id, caption=message.caption or "")
            elif message.content_type == "text":
                await bot.send_message(chat_id=user_id, text=message.text)
        except Exception as e:
            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)