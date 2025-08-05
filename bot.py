import json
import os
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = os.getenv("API_TOKEN")  # или замени напрямую: 'your_token_here'
bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)

USERS_FILE = "users.json"

# Загрузка пользователей
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

# Сохранение пользователей
def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)

# Обработка команды /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    save_user(message.from_user.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Каналы")
    await message.answer("👋 Добро пожаловать!\nНажмите <b>Каналы</b>, чтобы перейти к списку.", reply_markup=keyboard)

# Обработка кнопки "Каналы"
@dp.message_handler(lambda msg: msg.text == "Каналы")
async def show_channels(message: types.Message):
    inline = types.InlineKeyboardMarkup(row_width=1)
    inline.add(
        types.InlineKeyboardButton("Спорт", url="https://t.me/sportsoda"),
        types.InlineKeyboardButton("Профком", url="https://t.me/profkomsoda"),
        types.InlineKeyboardButton("ОТиПБ", url="https://t.me/your_invest_channel"),
        types.InlineKeyboardButton("Фабрика идей", url="https://t.me/your_invest_channel"),
        types.InlineKeyboardButton("Что такое БСА", url="https://t.me/your_invest_channel"),
    )
    await message.answer("Выберите канал:", reply_markup=inline)

# Пересылка постов из каналов
@dp.channel_post_handler()
async def forward_to_users(post: types.Message):
    users = load_users()

    # Получаем название канала
    try:
        channel = await bot.get_chat(post.chat.id)
        from_info = f"<b>📢 Канал:</b> {channel.title}\n\n"
    except:
        from_info = ""

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

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
