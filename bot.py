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
            if post.content_type == 'photo':
                await bot.send_photo(
                    user_id,
                    photo=post.photo[-1].file_id,
                    caption=from_info + (post.caption or ""),
                    parse_mode="HTML"
                )
            elif post.content_type == 'video':
                await bot.send_video(
                    user_id,
                    video=post.video.file_id,
                    caption=from_info + (post.caption or ""),
                    parse_mode="HTML"
                )
            elif post.content_type == 'text':
                await bot.send_message(
                    user_id,
                    from_info + post.text,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    user_id,
                    f"{from_info}📌 Новый пост в канале (тип: {post.content_type})",
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"❌ Ошибка при рассылке пользователю {user_id}: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
