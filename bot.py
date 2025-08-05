from aiogram import Bot, Dispatcher, executor, types

import os
API_TOKEN = os.getenv("API_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Спорт", url="https://t.me/sportsoda"))
    keyboard.add(types.InlineKeyboardButton(text="Новости Профкома", url="https://t.me/profkomsoda"))
    keyboard.add(types.InlineKeyboardButton(text="ОТиПБ", url="https://t.me/your_invest_channel"))
    keyboard.add(types.InlineKeyboardButton(text="Фабрика идей", url="https://t.me/your_invest_channel"))
    keyboard.add(types.InlineKeyboardButton(text="Что такое БСА", url="https://t.me/your_invest_channel"))
    await message.answer("Выберите интересующую вас тему:", reply_markup=keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)