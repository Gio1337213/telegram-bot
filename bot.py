from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart
import os
import json

API_TOKEN = os.getenv("API_TOKEN") or "YOUR_API_TOKEN"
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Файл подписчиков
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    with open(SUBSCRIBERS_FILE, "r") as f:
        return json.load(f)

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f)

# Реплай-кнопка "Каналы"
menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.add(KeyboardButton("📢 Каналы"))

# Инлайн-кнопки со ссылками на каналы
inline_links = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton(text="Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton(text="Новости Профкома", url="https://t.me/profkomsoda"),
    InlineKeyboardButton(text="ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton(text="Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton(text="Что такое БСА", url="https://t.me/your_invest_channel")
)

@dp.message_handler(CommandStart())
async def start_handler(message: types.Message):
    subscribers = load_subscribers()
    if message.from_user.id not in subscribers:
        subscribers.append(message.from_user.id)
        save_subscribers(subscribers)

    photo_path = "welcome.jpg"
    caption = "👋 Добро пожаловать! Нажмите 📢 Каналы, чтобы выбрать интересующий."

    try:
        with open(photo_path, "rb") as photo:
            await message.answer_photo(photo, caption=caption, reply_markup=menu_keyboard)
    except FileNotFoundError:
        await message.answer(caption, reply_markup=menu_keyboard)

@dp.message_handler(lambda msg: msg.text == "📢 Каналы")
async def send_inline_links(message: types.Message):
    await message.answer("Выберите канал:", reply_markup=inline_links)

# Рассылка новых постов из канала подписчикам
@dp.channel_post_handler()
async def channel_post_handler(message: types.Message):
    text = f"🆕 Новость из канала:\n\n{message.text or 'Без текста'}"
    subscribers = load_subscribers()
    for user_id in subscribers:
        try:
            await bot.send_message(chat_id=user_id, text=text)
        except:
            continue

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)