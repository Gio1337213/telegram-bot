import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart

API_TOKEN = os.getenv("API_TOKEN")
USERS_FILE = "users.json"

bot = Bot(token=API_TOKEN, parse_mode="HTML")  # глобально ставим HTML
dp = Dispatcher(bot)

# Реплай-кнопка
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

# Создание файла users.json при необходимости
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# /start — добавление юзера
@dp.message_handler(CommandStart())
async def send_welcome(message: types.Message):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    if message.from_user.id not in users:
        users.append(message.from_user.id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

    await message.answer("👋 Добро пожаловать!\n\nНажмите кнопку ниже:", reply_markup=reply_kb)

# Кнопка "Каналы"
@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def show_channels(msg: types.Message):
    await msg.answer("Выберите канал:", reply_markup=inline_kb)

# Обработка сообщений из канала (бот должен быть админом)
@dp.channel_post_handler()
async def forward_channel_post(message: types.Message):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    # Подпись с названием канала
    channel_title = message.chat.title
    base_caption = f"📣 <b>Пост из канала:</b> <i>{channel_title}</i>\n\n"

    # Определение финального текста
    content_text = message.caption or message.text or ""
    full_caption = base_caption + content_text

    # Срезаем если длинный caption
    if len(full_caption) > 1024:
        full_caption = full_caption[:1020] + "..."

    for user_id in users:
        try:
            if message.content_type == "photo":
                await bot.send_photo(user_id, message.photo[-1].file_id, caption=full_caption)
            elif message.content_type == "video":
                await bot.send_video(user_id, message.video.file_id, caption=full_caption)
            elif message.content_type == "document":
                await bot.send_document(user_id, message.document.file_id, caption=full_caption)
            elif message.content_type == "text":
                await bot.send_message(user_id, full_caption)
        except Exception as e:
            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")
