"""Сокращение ссылок (/shorten) через сервис is.gd."""


from aiogram import Router, types
from aiogram.filters import Command
from services.shorten_api import shorten_url
import logging
from handlers.stats import record_command

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("shorten"))
async def cmd_shorten(message: types.Message) -> None:
    """Сокращает переданную ссылку и возвращает короткую версию.

    Args:
        message: Входящее сообщение.
    """
    args = message.text.split(maxsplit=1)
    if len(args) <2:
        logger.debug(f"User {message.from_user.id} used /shorten without URL")
        await message.answer("Использование: /shorten https://длинная-ссылка.ru")
        return
    
    long_url = args[1].strip()
    # Валидация
    if not (long_url.startswith("http://") or long_url.startswith("https://")):
        logger.warning(f"User {message.from_user.id} provided invalid URL format: {long_url}")
        await message.answer("Ссылка должна начинаться с http:// или https://")
        return
    
    logger.debug(f"User {message.from_user.id} requests shortening of: {long_url}")
    short = await shorten_url(long_url)
    if short:
        await message.answer(f"Короткая ссылка: {short}")
        logger.info(f"Shortened URL for user {message.from_user.id}: {short}")
        record_command(message.from_user.id, "/shorten")
    else:
        logger.error(f"Shortening failed for user {message.from_user.id}, URL: {long_url}")
        await message.answer("Ошибка при сокращении. Проверьте ссылку и попробуйте снова.")