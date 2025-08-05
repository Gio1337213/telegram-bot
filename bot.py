import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

API_TOKEN = os.getenv("API_TOKEN")  # Используется переменная окружения

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

USERS_FILE = "users.json"

# Кнопка "Каналы"
menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.add(KeyboardButton("Каналы"))


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    # Сохраняем пользователя
    user_id = message.from_user.id
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    else:
        users = []

    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

    # Приветствие
    caption = "👋 Добро пожаловать!\nВыберите действие:"
    photo_path = "welcome.jpg"

    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as photo:
            await message.answer_photo(photo, caption=caption, reply_markup=menu_keyboard)
    else:
        await message.answer(caption, reply_markup=menu_keyboard)


@dp.message_handler(lambda msg: msg.text == "Каналы")
async def show_channels(message: types.Message):
    inline_kb = InlineKeyboardMarkup(row_width=1)
    inline_kb.add(
        InlineKeyboardButton("Спорт", url="https://t.me/sportsoda"),
        InlineKeyboardButton("Новости Профкома", url="https://t.me/profkomsoda"),
        InlineKeyboardButton("ОТиПБ", url="https://t.me/your_invest_channel"),
        InlineKeyboardButton("Фабрика идей", url="https://t.me/your_invest_channel"),
        InlineKeyboardButton("Что такое БСА", url="https://t.me/your_invest_channel")
    )
    await message.answer("📌 Наши каналы:", reply_markup=inline_kb)


@dp.channel_post_handler()
async def forward_channel_post(message: types.Message):
    if not os.path.exists(USERS_FILE):
        return

    with open(USERS_FILE, "r") as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            return

    # Получаем подпись канала
    channel_title = message.chat.title or "Канал"
    channel_username = message.chat.username
    channel_ref = f"@{channel_username}" if channel_username else channel_title
    footer = f"\n\n📢 Из канала: {channel_ref}"

    for user_id in users:
        try:
            if message.content_type == "photo":
                caption = (message.caption or "") + footer
                await bot.send_photo(chat_id=user_id, photo=message.photo[-1].file_id, caption=caption)
            elif message.content_type == "video":
                caption = (message.caption or "") + footer
                await bot.send_video(chat_id=user_id, video=message.video.file_id, caption=caption)
            elif message.content_type == "document":
                caption = (message.caption or "") + footer
                await bot.send_document(chat_id=user_id, document=message.document.file_id, caption=caption)
            elif message.content_type == "text":
                await bot.send_message(chat_id=user_id, text=message.text + footer)
        except Exception as e:
            print(f"❌ Не удалось отправить сообщение {user_id}: {e}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
