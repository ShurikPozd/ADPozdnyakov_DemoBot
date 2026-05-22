"""Обработчик команды погоды (/weather) с использованием OpenWeatherMap API.

Реализует FSM: запрашивает название города, затем показывает текущую погоду.
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.weather_api import get_weather
import logging
from handlers.stats import record_command
from keyboards import main_kb, get_cancel_kb

router = Router()
logger = logging.getLogger(__name__)


class WeatherStates(StatesGroup):
    """Состояния FSM для диалога погоды."""

    waiting_for_city = State()


@router.message(Command("weather"))
async def weather_start(message: types.Message, state: FSMContext) -> None:
    """Начинает диалог погоды, запрашивает название города.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    logger.info(f"User {message.from_user.id} started weather command")
    await state.set_state(WeatherStates.waiting_for_city)
    await message.answer("Введите название города: ", reply_markup=get_cancel_kb())


@router.message(WeatherStates.waiting_for_city)
async def process_weather(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает ввод города, получает данные о погоде и отправляет результат.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM (очищается после ответа).
    """
    if message.text.startswith("/"):
        await state.clear()
        await message.answer("Диалог отменён. Отправьте команду заново.", reply_markup=main_kb)
        return
    city = message.text.strip()
    logger.debug(f"User {message.from_user.id} requested weather for city: {city}")
    data = await get_weather(city)
    if data:
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        desc = data["weather"][0]["description"].capitalize()
        answer = (
            f"Погода в городе {city.capitalize()}:\n"
            f"Температура: {temp}°C (ощущается как {feels_like}°C)\n"
            f"Влажность: {humidity}%\n"
            f"Ветер: {wind} м/с\n"
            f"{desc}"
        )
        await message.answer(answer, reply_markup=main_kb)
        logger.info(f"Weather for {city} sent to user {message.from_user.id}")
        record_command(message.from_user.id, "/weather")
    else:
        logger.warning(
            f"Weather not found for city: {city}, user {message.from_user.id}"
        )
        await message.answer(f"Город '{city.capitalize()}' не найден.", reply_markup=main_kb)
    await state.clear()
