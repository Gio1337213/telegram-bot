from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("💡 Канал по саморазвитию", url="https://t.me/selfdev_channel"),
        InlineKeyboardButton("📈 Канал про инвестиции", url="https://t.me/invest_channel"),
        InlineKeyboardButton("🧠 Канал про психологию", url="https://t.me/psychology_channel")
    )
    await message.answer("Выберите интересующий вас канал 👇", reply_markup=keyboard)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)