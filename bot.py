import os
import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

USERS_FILE = 'users.json'


def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f)


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    save_user(message.chat.id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📢 Каналы"))

    await message.answer("Добро пожаловать! Нажмите кнопку ниже, чтобы увидеть каналы:", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "📢 Каналы")
async def show_channels(message: types.Message):
    inline_kb = types.InlineKeyboardMarkup(row_width=1)
    inline_kb.add(
        types.InlineKeyboardButton(text="Спорт", url="https://t.me/sportsoda"),
        types.InlineKeyboardButton(text="Профком", url="https://t.me/profkomsoda"),
        types.InlineKeyboardButton(text="ОТиПБ", url="https://t.me/your_invest_channel"),
    )
    await message.answer("Выберите канал:", reply_markup=inline_kb)


# 📤 Рассылка при получении поста из канала
@dp.channel_post_handler(content_types=types.ContentType.ANY)
async def repost_to_users(post: types.Message):
    users = load_users()

    channel_name = post.chat.title or "Канал"

    for user_id in users:
        try:
            if post.text:
                text = f"📢 <b>{channel_name}</b>\n\n{post.text}"
                await bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")

            elif post.photo:
                file = await post.photo[-1].download(destination_file="temp.jpg")
                caption = f"📢 <b>{channel_name}</b>\n\n{post.caption or ''}"
                with open("temp.jpg", "rb") as photo:
                    await bot.send_photo(chat_id=user_id, photo=photo, caption=caption, parse_mode="HTML")
                os.remove("temp.jpg")

            elif post.video:
                file = await post.video.download(destination_file="temp.mp4")
                caption = f"📢 <b>{channel_name}</b>\n\n{post.caption or ''}"
                with open("temp.mp4", "rb") as video:
                    await bot.send_video(chat_id=user_id, video=video, caption=caption, parse_mode="HTML")
                os.remove("temp.mp4")

            await asyncio.sleep(1.5)  # ⚠️ Антифлуд задержка

        except Exception as e:
            logging.exception(f"Ошибка при отправке пользователю {user_id}: {e}")
