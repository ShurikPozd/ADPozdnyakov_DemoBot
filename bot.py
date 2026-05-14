import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton
import requests
import random
import string


# настройки
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


# клавиатура
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/weather"), KeyboardButton(text="/currency")]
    ],
    resize_keyboard=True
)


# /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Это демонстрационный бот А.Д. Позднякова.\n"
        "Доступные команды:\n"
        "/weather - погода\n"
        "/currency - конвертер валют\n"
        "/help - список команд",
        reply_markup=main_kb
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)


# /weather
@dp.message(Command("weather"))
async def weather_start(message: types.Message):
    await message.answer("Введите название города: ")

@dp.message()
async def show_weather(message: types.Message):
    if message.text.startswith('/'):
        return
    city = message.text.strip()
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    temp = data['main']['temp']
                    feels_like = data['main']['feels_like']
                    humidity = data['main']['humidity']
                    wind = data['wind']['speed']
                    desc = data['weather'][0]['description'].capitalize()
                    answer = (f"Погода в {city}:\n"
                            f"Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                            f"Влажность: {humidity}%\n"
                            f"Ветер: {wind} м/с\n"
                            f"{desc}")
                    await message.answer(answer)
                else:
                    await message.answer(f"Город '{city}' не найден. Попробуйте английское название.")
        except Exception as e:
            await message.answer(f"Ошибка: {type(e).__name__}. Проверьте интернет и ключ API.")    


# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())