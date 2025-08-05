from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import json
import os

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Загружаем список пользователей
def load_users():
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            return json.load(f)
    return []

# Сохраняем пользователей
def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open("users.json", "w") as f:
            json.dump(users, f)

# Регистрируем пользователей
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    save_user(message.chat.id)
    await message.answer("✅ Вы подписались на рассылку.")

# Принимаем пост из канала
@dp.channel_post_handler()
async def channel_post_handler(message: types.Message):
    users = load_users()
    channel_name = message.chat.title  # Название канала
    caption = message.caption or message.text or ""
    caption = f"📢 <b>{channel_name}</b>\n\n{caption}"

    for user_id in users:
        try:
            # Фото
            if message.photo:
                await bot.send_photo(
                    user_id,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            # Видео
            elif message.video:
                await bot.send_video(
                    user_id,
                    video=message.video.file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            # Документ
            elif message.document:
                await bot.send_document(
                    user_id,
                    document=message.document.file_id,
                    caption=caption,
                    parse_mode="HTML"
                )
            # Текст
            elif message.text:
                await bot.send_message(user_id, caption, parse_mode="HTML")

        except Exception as e:
            print(f"❌ Ошибка отправки пользователю {user_id}: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
