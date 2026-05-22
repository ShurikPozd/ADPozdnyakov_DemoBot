"""Сокращение ссылок (/shorten) через сервис is.gd.

Реализует FSM: запрашивает URL, сокращает.
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.shorten_api import shorten_url
import logging
from handlers.stats import record_command

router = Router()
logger = logging.getLogger(__name__)


class ShortenStates(StatesGroup):
    waiting_for_url = State()


@router.message(Command("shorten"))
async def shorten_start(message: types.Message, state: FSMContext) -> None:
    """Начинает диалог сокращения ссылки, запрашивает URL."""
    logger.info(f"Пользователь {message.from_user.id} отправил команду /shorten")
    await state.set_state(ShortenStates.waiting_for_url)
    await message.answer("Отправьте ссылку (должна начинаться с http:// или https://).")


@router.message(ShortenStates.waiting_for_url)
async def process_shorten(message: types.Message, state: FSMContext) -> None:
    """Сокращает полученный URL и отправляет результат."""
    if message.text.startswith("/"):
        await state.clear()
        await message.answer("Диалог отменён. Отправьте команду заново.")
        return
    long_url = message.text.strip()
    if not (long_url.startswith("http://") or long_url.startswith("https://")):
        await message.answer(
            "Ссылка должна начинаться с http:// или https://. Попробуйте ещё раз."
        )
        return

    logger.debug(
        f"Пользователь {message.from_user.id} отправил запрос на сокращение: {long_url}"
    )
    short = await shorten_url(long_url)
    if short:
        await message.answer(f"Короткая ссылка: {short}")
        logger.info(
            f"URL {long_url} сокращён для пользователя {message.from_user.id}: {short}"
        )
        record_command(message.from_user.id, "/shorten")
    else:
        logger.error(
            f"Сокращение ссылки провалилось для пользователя {message.from_user.id}, URL: {long_url}"
        )
        await message.answer(
            "Ошибка при сокращении. Проверьте ссылку и попробуйте снова."
        )

    await state.clear()
