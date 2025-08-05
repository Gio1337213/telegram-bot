from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo
from aiogram.utils.exceptions import BotBlocked
import logging
import os
import json

API_TOKEN = os.getenv("API_TOKEN")  # Храните токен в Render → Environment

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

USERS_FILE = "users.json"
MEDIA_GROUP_CACHE = {}

# --- УПРАВЛЕНИЕ ПОДПИСЧИКАМИ ---

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

# --- КНОПКИ ---

reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
reply_keyboard.add(KeyboardButton("📢 Каналы"))

inline_keyboard = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton(text="⚽ Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton(text="📣 Новости Профкома", url="https://t.me/profkomsoda"),
    InlineKeyboardButton(text="💡 Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton(text="❓ Что такое БСА", url="https://t.me/your_invest_channel"),
)

# --- ХЭНДЛЕРЫ ---

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    save_user(message.from_user.id)
    caption = "👋 Добро пожаловать! Нажмите «Каналы» для перехода к темам."
    photo_path = "welcome.jpg"
    if os.path.exists(photo_path):
        with open(photo_path, 'rb') as photo:
            await message.answer_photo(photo, caption=caption, reply_markup=reply_keyboard)
    else:
        await message.answer(caption, reply_markup=reply_keyboard)

@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def show_channels(message: types.Message):
    await message.answer("Выберите интересующий канал:", reply_markup=inline_keyboard)

# --- ОБРАБОТКА КАНАЛОВ ---

@dp.channel_post_handler(content_types=types.ContentType.ANY)
async def repost_channel_post(message: types.Message):
    users = load_users()

    # Обработка альбомов (media groups)
    if message.media_group_id:
        MEDIA_GROUP_CACHE.setdefault(message.media_group_id, []).append(message)
        await asyncio.sleep(1.2)  # подождать поступление всех сообщений альбома

        if len(MEDIA_GROUP_CACHE[message.media_group_id]) > 1:
            group = MEDIA_GROUP_CACHE.pop(message.media_group_id)
            media = []
            for msg in group:
                if msg.photo:
                    media.append(InputMediaPhoto(media=msg.photo[-1].file_id, caption=msg.caption or ""))
                elif msg.video:
                    media.append(InputMediaVideo(media=msg.video.file_id, caption=msg.caption or ""))
            for user_id in users:
                try:
                    await bot.send_media_group(user_id, media)
                except Exception as e:
                    print(f"Ошибка у {user_id}: {e}")
            return  # уже обработали

    # Одиночные сообщения
    for user_id in users:
        try:
            if message.text:
                await bot.send_message(user_id, message.text)
            elif message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
            elif message.video:
                await bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
            elif message.document:
                await bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
            elif message.animation:
                await bot.send_animation(user_id, message.animation.file_id, caption=message.caption or "")
            else:
                print(f"Необработанный тип сообщения: {message.content_type}")
        except BotBlocked:
            print(f"Пользователь {user_id} заблокировал бота.")
        except Exception as e:
            print(f"Ошибка у {user_id}: {e}")

# --- СТАРТ ---

if __name__ == '__main__':
    import asyncio
    executor.start_polling(dp, skip_updates=True)
