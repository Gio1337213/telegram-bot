from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import os

API_TOKEN = os.getenv("API_TOKEN")
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Реплай-кнопки (горизонтальные строки)
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

row1 = [KeyboardButton("Спорт"), KeyboardButton("Новости Профкома")]
row2 = [KeyboardButton("ОТиПБ"), KeyboardButton("Фабрика идей")]
row3 = [KeyboardButton("Что такое БСА")]

keyboard.row(*row1)
keyboard.row(*row2)
keyboard.row(*row3)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    caption = "👋 Добро пожаловать в наш бот! Выберите интересующую вас тему ниже:"
    photo_path = "welcome.jpg"  # Убедись, что файл есть

    try:
        with open(photo_path, 'rb') as photo:
            await message.answer_photo(photo=photo, caption=caption, reply_markup=keyboard)
    except FileNotFoundError:
        await message.answer(caption, reply_markup=keyboard)

# Обработка нажатий на кнопки
@dp.message_handler(lambda message: message.text == "Спорт")
async def handle_sport(message: types.Message):
    await message.answer("Ссылка на спорт-канал: https://t.me/sportsoda")

@dp.message_handler(lambda message: message.text == "Новости Профкома")
async def handle_news(message: types.Message):
    await message.answer("Ссылка на новости профкома: https://t.me/profkomsoda")

@dp.message_handler(lambda message: message.text == "ОТиПБ")
async def handle_otipb(message: types.Message):
    await message.answer("Ссылка на ОТиПБ: https://t.me/your_invest_channel")

@dp.message_handler(lambda message: message.text == "Фабрика идей")
async def handle_factory(message: types.Message):
    await message.answer("Ссылка на фабрику идей: https://t.me/your_invest_channel")

@dp.message_handler(lambda message: message.text == "Что такое БСА")
async def handle_bsa(message: types.Message):
    await message.answer("Ссылка на БСА: https://t.me/your_invest_channel")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
