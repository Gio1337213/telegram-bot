from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import aiohttp
import os
import json

API_TOKEN = os.getenv("API_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Файл с базой пользователей
USERS_FILE = "users.json"
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
else:
    users = []

# --- Клавиатуры ---
reply_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
reply_keyboard.add(types.KeyboardButton("📢 Каналы"))

inline_keyboard = types.InlineKeyboardMarkup(row_width=1)
inline_keyboard.add(
    types.InlineKeyboardButton("Спорт", url="https://t.me/sportsoda"),
    types.InlineKeyboardButton("Новости Профкома", url="https://t.me/profkomsoda"),
    types.InlineKeyboardButton("Фабрика идей", url="https://t.me/your_invest_channel"),
)

# --- Команда /start ---
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    if message.from_user.id not in users:
        users.append(message.from_user.id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)
    await message.answer("👋 Добро пожаловать! Используйте кнопки в меню ниже.", reply_markup=reply_keyboard)

# --- Обработка нажатия на кнопку "Каналы" ---
@dp.message_handler(lambda message: message.text == "📢 Каналы")
async def channels_handler(message: types.Message):
    await message.answer("Выберите канал из списка:", reply_markup=inline_keyboard)

# --- Хендлер пересылки новых постов из каналов ---
@dp.channel_post_handler(content_types=types.ContentType.ANY)
async def channel_post_handler(message: types.Message):
    channel_title = message.chat.title
    caption = f"📢 От канала: {channel_title}\n\n{message.caption or ''}"

    for user_id in users:
        try:
            if message.content_type == types.ContentType.TEXT:
                await bot.send_message(user_id, caption)

            elif message.content_type == types.ContentType.PHOTO:
                file_id = message.photo[-1].file_id
                await send_downloaded_file(user_id, file_id, "jpg", caption)

            elif message.content_type == types.ContentType.VIDEO:
                file_id = message.video.file_id
                await send_downloaded_file(user_id, file_id, "mp4", caption, is_video=True)

            # Можно добавить и другие типы сообщений (documents, audios и т.д.)

        except Exception as e:
            print(f"Ошибка при отправке пользователю {user_id}: {e}")

# --- Функция скачивания и пересылки файла ---
async def send_downloaded_file(user_id, file_id, extension, caption, is_video=False):
    file = await bot.get_file(file_id)
    file_path = file.file_path
    url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_path}"

    temp_file = f"temp.{extension}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(temp_file, "wb") as f:
                    f.write(await resp.read())

    with open(temp_file, "rb") as f:
        if is_video:
            await bot.send_video(user_id, f, caption=caption)
        else:
            await bot.send_photo(user_id, f, caption=caption)

    os.remove(temp_file)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
