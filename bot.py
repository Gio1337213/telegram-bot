import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart

API_TOKEN = os.getenv("API_TOKEN")  # Обязательно добавь в Render или .env
USERS_FILE = "users.json"
WELCOME_IMAGE = "welcome.jpg"

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Реплай-кнопка
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reply_kb.add(KeyboardButton("📢 Каналы"))

# Инлайн-кнопки
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("⚽ Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("📣 Профком", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("⚠️ ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("💡 Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("❓ Что такое БСА", url="https://t.me/your_invest_channel")
)

# Создание users.json при необходимости
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# /start — добавление юзера + приветствие с картинкой
@dp.message_handler(CommandStart())
async def send_welcome(message: types.Message):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    if message.from_user.id not in users:
        users.append(message.from_user.id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

    caption = "👋 Добро пожаловать!\n\nНажмите кнопку ниже, чтобы открыть меню:"
    try:
        with open(WELCOME_IMAGE, "rb") as photo:
            await message.answer_photo(photo, caption=caption, reply_markup=reply_kb)
    except FileNotFoundError:
        await message.answer(caption, reply_markup=reply_kb)

# Кнопка "📢 Каналы"
@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def show_channels(msg: types.Message):
    await msg.answer("Выберите интересующий канал:", reply_markup=inline_kb)

# Пересылка постов из каналов
@dp.channel_post_handler()
async def forward_to_users(post: types.Message):
    users = load_users()

    # Подпись для заголовка (если доступен channel username/title)
    try:
        channel = await bot.get_chat(post.chat.id)
        from_info = f"<b>📢 Канал:</b> {channel.title}\n\n"
    except:
        from_info = ""

    for user_id in users:
        try:
            if post.text:
                await bot.send_message(user_id, from_info + post.text)
            elif post.photo:
                await bot.send_photo(user_id, post.photo[-1].file_id, caption=from_info + (post.caption or ""))
            elif post.video:
                await bot.send_video(user_id, post.video.file_id, caption=from_info + (post.caption or ""))
            elif post.document:
                await bot.send_document(user_id, post.document.file_id, caption=from_info + (post.caption or ""))
            elif post.animation:
                await bot.send_animation(user_id, post.animation.file_id, caption=from_info + (post.caption or ""))
            else:
                await bot.send_message(user_id, f"{from_info}📌 Новый пост в канале.")
        except Exception as e:
            print(f"❌ Ошибка при отправке пользователю {user_id}: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
