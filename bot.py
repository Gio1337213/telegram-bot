import os
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import CommandStart

API_TOKEN = os.getenv("API_TOKEN")
USERS_FILE = "users.json"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Реплай-клавиатура
reply_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reply_kb.add(KeyboardButton("📢 Каналы"))

# Инлайн-кнопки
inline_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("Новости Профкома", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("Что такое БСА", url="https://t.me/your_invest_channel")
)

# Убедись, что файл users.json существует
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# Команда /start
@dp.message_handler(CommandStart())
async def send_welcome(message: types.Message):
    # Добавляем пользователя в users.json
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    if message.from_user.id not in users:
        users.append(message.from_user.id)
        with open(USERS_FILE, "w") as f:
            json.dump(users, f)

    # Приветствие
    caption = "👋 Добро пожаловать!\n\nНажмите кнопку ниже, чтобы выбрать канал:"
    await message.answer(caption, reply_markup=reply_kb)

# Обработка кнопки "Каналы"
@dp.message_handler(lambda message: message.text == "📢 Каналы")
async def show_channels(message: types.Message):
    await message.answer("Выберите канал:", reply_markup=inline_kb)

# РАССЫЛКА из канала — бот должен быть админом!
@dp.channel_post_handler()
async def forward_channel_post(message: types.Message):
    users = load_users()
    channel_name = message.chat.title or "Канал"
    caption = f"📢 <b>{channel_name}</b>\n\n{message.caption or message.text or ''}"

    for user_id in users:
        try:
            if message.photo:
                file = await bot.get_file(message.photo[-1].file_id)
                photo_path = f"photo_{message.message_id}.jpg"
                await message.photo[-1].download(destination_file=photo_path)
                with open(photo_path, "rb") as photo_file:
                    await bot.send_photo(user_id, photo=photo_file, caption=caption, parse_mode="HTML")
                os.remove(photo_path)

            elif message.video:
                file = await bot.get_file(message.video.file_id)
                video_path = f"video_{message.message_id}.mp4"
                await message.video.download(destination_file=video_path)
                with open(video_path, "rb") as video_file:
                    await bot.send_video(user_id, video=video_file, caption=caption, parse_mode="HTML")
                os.remove(video_path)

            elif message.document:
                file = await bot.get_file(message.document.file_id)
                doc_path = f"doc_{message.message_id}.pdf"
                await message.document.download(destination_file=doc_path)
                with open(doc_path, "rb") as doc_file:
                    await bot.send_document(user_id, document=doc_file, caption=caption, parse_mode="HTML")
                os.remove(doc_path)

            elif message.text:
                await bot.send_message(user_id, text=caption, parse_mode="HTML")

            await asyncio.sleep(1.5)  # антифлуд

        except Exception as e:
            logging.error(f"Ошибка рассылки для {user_id}: {e}")