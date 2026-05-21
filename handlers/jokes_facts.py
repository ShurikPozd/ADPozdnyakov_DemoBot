"""Команды для получения случайных шуток (/joke) и интересных фактов (/fact).

Использует JokeAPI и Useless Facts API.
"""

from aiogram import Router, types
from aiogram.filters import Command
from services.jokes_facts_api import get_random_joke, get_random_fact
import logging
from handlers.stats import record_command

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("joke"))
async def cmd_joke(message: types.Message) -> None:
    """Отправляет случайную шутку."""
    logger.info(f"User {message.from_user.id} requested a joke")
    joke = await get_random_joke()
    if joke:
        await message.answer(joke)
        logger.debug(f"Joke sent to user {message.from_user.id}")
        record_command(message.from_user.id, "/joke")
    else:
        logger.error(f"Failed to fetch joke for user {message.from_user.id}")
        await message.answer("Не удалось получить шутку. Попробуйте позже.")


@router.message(Command("fact"))
async def cmd_fact(message: types.Message) -> None:
    """Отправляет случайный интересный факт."""
    logger.info(f"User {message.from_user.id} requested a fact")
    fact = await get_random_fact()
    if fact:
        await message.answer(fact)
        logger.debug(f"Fact sent to user {message.from_user.id}")
        record_command(message.from_user.id, "/fact")
    else:
        logger.error(f"Failed to fetch fact for user {message.from_user.id}")
        await message.answer("Не удалось получить интересный факт. Попробуйте позже.")
