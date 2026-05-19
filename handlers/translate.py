# handlers/translate.py
from aiogram import Router, types
from aiogram.filters import Command
from services.translate_api import translate_text
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("translate"))
async def cmd_translate(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        logger.debug(f"User {message.from_user.id} used /translate without text")
        await message.answer("Использование: /translate <текст для перевода на русский>")
        return

    text = args[1].strip()
    if len(text) > 500:
        logger.warning(f"User {message.from_user.id} sent text that's too long: ({len(text)} chars)")
        await message.answer("Текст слишком длинный (макс. 500 символов).")
        return

    # Перевод на русский язык
    logger.debug(f"User {message.from_user.id} requests translation of: {text[:50]}...")
    translated = await translate_text(text, target_lang="ru")
    if translated:
        await message.answer(f"Перевод:\n{translated}")
        logger.info(f"Translation sent to user {message.from_user.id}")
    else:
        logger.error(f"Translation failed for user {message.from_user.id}")
        await message.answer("Не удалось перевести. Попробуйте позже.")