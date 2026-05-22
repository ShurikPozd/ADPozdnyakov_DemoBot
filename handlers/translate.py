"""Перевод текста (/translate) с использованием googletrans.

Реализует FSM: запрашивает текст, переводит на русский.
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.translate_api import translate_text
import logging
from handlers.stats import record_command

router = Router()
logger = logging.getLogger(__name__)

class TranslateStates(StatesGroup):
    waiting_for_text = State()


@router.message(Command("translate"))
async def translate_start(message: types.Message, state: FSMContext) -> None:
    """Начинает диалог перевода, запрашивает текст."""
    logger.info(f"Пользователь {message.from_user.id} отправил команду /translate")
    await state.set_state(TranslateStates.waiting_for_text)
    await message.answer("Отправьте текст, который нужно перевести на русский язык.\n"
                         "Язык оригинала определится автоматически.")

@router.message(TranslateStates.waiting_for_text)
async def process_translate(message: types.Message, state: FSMContext) -> None:
    """Переводит полученный текст и отправляет результат."""
    if message.text.startswith('/'):
        await state.clear()
        await message.answer("Диалог отменён. Отправьте команду заново.")
        return
    text = message.text.strip()
    if not text:
        await message.answer("Пожалуйста, отправьте текст")
        return

    if len(text) > 500:
        logger.warning(
            f"Пользователь {message.from_user.id} отправил слишком длинный текст: ({len(text)} символов)"
        )
        await message.answer("Текст слишком длинный (макс. 500 символов).")
        return

    # Перевод на русский язык
    logger.debug(f"Пользователь {message.from_user.id} запросил перевод: {text[:50]}...")
    translated = await translate_text(text, target_lang="ru")
    if translated:
        await message.answer(f"Перевод:\n{translated}")
        logger.info(f"Перевод отправлен пользователю {message.from_user.id}")
        record_command(message.from_user.id, "/translate")
    else:
        logger.error(f"Перевод для пользователя {message.from_user.id} не удался")
        await message.answer("Не удалось перевести. Попробуйте позже.")

    await state.clear()
