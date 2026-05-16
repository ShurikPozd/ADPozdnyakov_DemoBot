import os
import json
import logging
import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup,KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage


# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
OWM_API_KEY = os.getenv("OWM_API_KEY")

# Настройки
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Клавиатура
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/weather"), KeyboardButton(text="/currency")],
        [KeyboardButton(text="/help")]
    ],
    resize_keyboard=True
)


# Состояния для погоды
class WeatherStates(StatesGroup):
    waiting_for_city = State()

# Состояния для конвертера валют
class CurrencyStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_from_currency = State()
    waiting_for_to_currency = State()

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
async def weather_start(message: types.Message, state: FSMContext):
    await state.set_state(WeatherStates.waiting_for_city)
    await message.answer("Введите название города: ")

@dp.message(WeatherStates.waiting_for_city)
async def show_weather(message: types.Message, state: FSMContext):
    city = message.text.strip()
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                data = await response.json()
                if response.status == 200 and 'main' in data and 'weather' in data:
                    temp = data['main']['temp']
                    feels_like = data['main']['feels_like']
                    humidity = data['main']['humidity']
                    wind = data['wind']['speed']
                    desc = data['weather'][0]['description'].capitalize()
                    city_display = city.capitalize()
                    answer = (f"Погода в городе {city_display}:\n"
                            f"Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                            f"Влажность: {humidity}%\n"
                            f"Ветер: {wind} м/с\n"
                            f"{desc}")
                    await message.answer(answer)
                else:
                    await message.answer(f"Город '{city}' не найден. Попробуйте английское название.")
        except Exception as e:
            await message.answer(f"Ошибка: {type(e).__name__}. Проверьте интернет и ключ API.")    
    await state.clear()


# Конвертер через ЦБ РФ
async def get_cbr_rates():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                text = await response.text()
                data = json.loads(text)
                rates = {}
                rates['RUB'] = 1.0
                for code, info in data['Valute'].items():
                    nominal = info['Nominal']
                    value = info['Value']
                    rates[code] = value / nominal
                return rates
            else:
                return None
            
def convert_currency(amount, from_cur, to_cur, rates):
    if from_cur not in rates or to_cur not in rates:
        return None
    rub_amount = amount * rates[from_cur]
    result = rub_amount / rates[to_cur]
    return round(result,2)


# /currency

# @dp.message(Command("currency"))
# async def currency_start(message: types.Message):
#     await message.answer("Кнопка работает!")

@dp.message(Command("currency"))
async def currency_start(message: types.Message, state: FSMContext):
    print("1. currency_start вызван")
    await state.set_state(CurrencyStates.waiting_for_amount)
    print("2. состояние установлено в waiting_for_amount")
    await message.answer("Введите сумму: ")

@dp.message(CurrencyStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    print("DEBUG: waiting_for_amount, текст:", message.text)
    try:
        amount = float(message.text.strip())
        await state.update_data(amount=amount)
        await state.set_state(CurrencyStates.waiting_for_from_currency)
        await message.answer("Введите исходную валюту (например, USD, EUR, RUB): ")
    except ValueError:
        await message.answer("Введите число или попробуйте ещё раз: ")

@dp.message(CurrencyStates.waiting_for_from_currency)
async def process_from_currency(message: types.Message, state: FSMContext):
    from_cur = message.text.strip().upper()
    await state.update_data(from_cur=from_cur)
    await state.set_state(CurrencyStates.waiting_for_to_currency)
    await message.answer("Введите целевую валюту: ")

@dp.message(CurrencyStates.waiting_for_to_currency)
async def process_to_currency(message: types.Message, state: FSMContext):
    to_cur = message.text.strip().upper()
    user_data = await state.get_data()
    amount = user_data['amount']
    from_cur = user_data['from_cur']

    # Получение курсов от ЦБ
    rates = await get_cbr_rates()
    if rates is None:
        await message.answer("Не удалось получить курсы валют. Попробуйте позже.")
        await state.clear()
        return
    
    if from_cur not in rates:
        await message.answer(f"Валюта {from_cur} не найдена. Попробуйте снова. Доступны: RUB, USD, EUR и др.")
        await state.clear()
        return
    
    if to_cur not in rates:
        await message.answer(f"Валюта {to_cur} не найдена. Попробуйте снова. Доступны: RUB, USD, EUR и др.")
        await state.clear()
        return
    
    result = convert_currency(amount, from_cur, to_cur, rates)
    await message.answer(f"{amount} {from_cur} = {result} {to_cur}\n (по курсу ЦБ РФ)")
    await state.clear()
    

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())