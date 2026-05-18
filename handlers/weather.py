from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.weather_api import get_weather


router = Router()


class WeatherStates(StatesGroup):
    waiting_for_city = State()


@router.message(Command("weather"))
async def weather_start(message: types.Message, state: FSMContext):
    await state.set_state(WeatherStates.waiting_for_city)
    await message.answer("Введите название города: ")


@router.message(WeatherStates.waiting_for_city)
async def process_weather(message: types.Message, state: FSMContext):
    city = message.text.strip()
    data = await get_weather(city)
    if data:
        temp = data['main']['temp']
        feels_like = data ['main']['feels_like']
        humidity = data['main']['humidity']
        wind = data['wind']['speed']
        desc = data['weather'][0]['description'].capitalize()
        answer = (f"Погода в городе {city.capitalize()}:\n"
                  f"Температура: {temp}°C (ощущается как {feels_like}°C)\n"
                  f"Влажность: {humidity}%\n"
                  f"Ветер: {wind} м/с\n"
                  f"{desc}")
        await message.answer(answer)
    else:
        await message.answer(f"Город '{city.capitalize()}' не найден.")
    await state.clear()