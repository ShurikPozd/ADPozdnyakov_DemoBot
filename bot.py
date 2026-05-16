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
        [KeyboardButton(text="/anime"), KeyboardButton(text="/help")]
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


# Состояния для распознавателя аниме-скриншотов
class AnimeStates(StatesGroup):
    waiting_for_photo = State()

# /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Это демонстрационный бот А.Д. Позднякова.\n"
        "Доступные команды:\n"
        "/weather - погода\n"
        "/currency - конвертер валют\n"
        "/anime - распознать из какого аниме скриншот\n"
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
async def process_weather(message: types.Message, state: FSMContext):
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
    

@dp.message(Command("anime"))
async def anime_start(message: types.Message, state: FSMContext):
    await state.set_state(AnimeStates.waiting_for_photo)
    await message.answer("Отправьте скриншот из аниме, попробую распознать.")


@dp.message(AnimeStates.waiting_for_photo)
async def process_anime_photo(message: types.Message, state: FSMContext, bot: Bot):
    if not message.photo:
        await message.answer("Отправьте изображение.")
        return
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)

    url = "https://api.trace.moe/search"
    async with aiohttp.ClientSession() as session:
        form = aiohttp.FormData()
        form.add_field('image', file_bytes, filename='anime.jpg', content_type='image/jpeg')

        try:
            async with session.post(url, data=form, timeout=15) as response:
                if response.status != 200:
                    await message.answer("Сервис временно недоступен. Попробуйте позже.")
                    await state.clear()
                    return
                data = await response.json()
                if not data.get("result"):
                    await message.answer("Не удалось распознать. Попробуйте другой скриншот.")
                    await state.clear()
                    return
                
                best = data["result"][0]
                similarity = best["similarity"] * 100
                title = (
                    best.get("filename") or
                    best.get("anime") or
                    best.get("title") or 
                    "Неизвестное аниме"
                )

                episode = best.get("episode")
                from_time = best.get("from")
                to_time = best.get("to")

                def format_time(seconds):
                    if seconds is None:
                        return "?"
                    mins = int(seconds // 60)
                    secs = int(seconds % 60)
                    return f"{mins:02d}:{secs:02d}"
                
                time_str = f"{format_time(from_time)} - {format_time(to_time)}" if from_time and to_time else "Неизвестно"

                answer = (
                    f"Название {title}\n"
                    f"Схожесть {similarity:.2f}%\n"
                    f"Эпизод: {episode if episode else 'неизвестен'}\n"
                    f"Тайм-код: {time_str}"
                )
                await message.answer(answer, parse_mode="Markdown")

        except aiohttp.ClientError as e:
            await message.answer(f"Ошибка сети: {type(e).__name__}. Попробуйте позже.")
        except Exception as e:
            await message.answer(f"Неизвестная ошибка: {type(e).__name__}.")
        finally:
            await state.clear()



# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())