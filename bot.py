import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import CommandStart
from aiogram.utils.exceptions import BotBlocked, ChatNotFound

API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

USERS_FILE = "users.json"

# Загружаем подписчиков из файла
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

# Сохраняем подписчика
def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

# Обработчик команды /start
@dp.message_handler(CommandStart())
async def handle_start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer("✅ Вы подписаны на рассылку новостей из наших каналов.")

# Хендлер постов из каналов
@dp.channel_post_handler()
async def handle_channel_post(message: types.Message):
    print("📩 Новое сообщение из канала:", message.chat.title)
    users = load_users()

    for user_id in users:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
        except (BotBlocked, ChatNotFound):
            print(f"⚠️ Пользователь {user_id} недоступен, удаляю из списка.")
            users.remove(user_id)
        except Exception as e:
            print(f"Ошибка при отправке пользователю {user_id}: {e}")

    # Обновляем файл пользователей, исключив недоступных
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
