import os
import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart

API_TOKEN = os.getenv("API_TOKEN")
USERS_FILE = "users.json"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# Создаем реплай клавиатуру
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reply_kb.add(KeyboardButton("📢 Каналы"))

# Инлайн клавиатура с каналами
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("Новости Профкома", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("Что такое БСА", url="https://t.me/your_invest_channel")
)


def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f)


@dp.message_handler(CommandStart())
async def send_welcome(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "👋 Добро пожаловать!\n\nНажмите кнопку ниже, чтобы выбрать канал:",
        reply_markup=reply_kb
    )


@dp.message_handler(lambda message: message.text == "📢 Каналы")
async def show_channels(message: types.Message):
    await message.answer("Выберите канал:", reply_markup=inline_kb)


@dp.channel_post_handler()
async def forward_channel_post(message: types.Message):
    users = load_users()
    channel_name = message.chat.title or "Канал"

    for user_id in users:
        try:
            caption = f"📢 <b>{channel_name}</b>\n\n{message.caption or message.text or ''}"

            if message.photo:
                await bot.send_photo(user_id, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")
            elif message.video:
                await bot.send_video(user_id, video=message.video.file_id, caption=caption, parse_mode="HTML")
            elif message.document:
                await bot.send_document(user_id, document=message.document.file_id, caption=caption, parse_mode="HTML")
            elif message.text:
                await bot.send_message(user_id, text=caption, parse_mode="HTML")

            await asyncio.sleep(1.2)  # антии-флуд пауза

        except Exception as e:
            logging.error(f"❌ Ошибка при отправке пользователю {user_id}: {e}")
