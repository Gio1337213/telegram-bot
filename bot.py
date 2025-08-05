import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = os.getenv("API_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

USERS_FILE = "users.txt"

# Загружаем список пользователей
def load_users():
    if not os.path.exists(USERS_FILE):
        return set()
    with open(USERS_FILE, 'r') as f:
        return set(map(int, f.read().split()))

# Добавляем нового пользователя
def save_user(user_id):
    users = load_users()
    if user_id not in users:
        with open(USERS_FILE, 'a') as f:
            f.write(f"{user_id}\n")

# Клавиатура: одна кнопка "Каналы"
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("📢 Каналы"))

# Inline кнопки-ссылки на каналы
inline_channels = InlineKeyboardMarkup(row_width=1)
inline_channels.add(
    InlineKeyboardButton("🏀 Спорт", url="https://t.me/sportsoda"),
    InlineKeyboardButton("🗞 Новости Профкома", url="https://t.me/profkomsoda"),
    InlineKeyboardButton("💼 ОТиПБ", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("💡 Фабрика идей", url="https://t.me/your_invest_channel"),
    InlineKeyboardButton("📘 Что такое БСА", url="https://t.me/your_invest_channel")
)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    save_user(message.from_user.id)
    caption = "👋 Добро пожаловать! Нажмите «Каналы», чтобы перейти к полезным ссылкам."
    with open("welcome.jpg", "rb") as photo:
        await message.answer_photo(photo, caption=caption, reply_markup=main_keyboard)

@dp.message_handler(lambda message: message.text == "📢 Каналы")
async def channels_handler(message: types.Message):
    await message.answer("🔗 Наши каналы:", reply_markup=inline_channels)

# Авторассылка новых постов из каналов
@dp.channel_post_handler()
async def handle_channel_post(message: types.Message):
    users = load_users()

    for user_id in users:
        try:
            if message.text:
                await bot.send_message(user_id, message.text)
            elif message.photo:
                await bot.send_photo(user_id, photo=message.photo[-1].file_id, caption=message.caption or "")
            elif message.video:
                await bot.send_video(user_id, video=message.video.file_id, caption=message.caption or "")
            elif message.document:
                await bot.send_document(user_id, document=message.document.file_id, caption=message.caption or "")
            elif message.animation:
                await bot.send_animation(user_id, animation=message.animation.file_id, caption=message.caption or "")
            else:
                print("Неизвестный тип сообщения")
        except Exception as e:
            print(f"Ошибка при отправке пользователю {user_id}: {e}")
            continue

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
