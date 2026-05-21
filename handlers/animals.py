from aiogram import Router, types
from aiogram.filters import Command
from services.animals_api import get_random_cat, get_random_dog
import logging
from handlers.stats import record_command

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("cat"))
async def cmd_cat(message: types.Message):
    logger.info(f"User {message.from_user.id} requested a cat picture")
    url = await get_random_cat()
    if url:
        await message.answer_photo(url, caption="Котик  /ᐠ - ˕ -マ")
        logger.debug(f"Cat picture sent to user {message.from_user.id}")
        record_command(message.from_user.id, "/cat")
    else:
        logger.error(f"Failed to fetch cat picture for user {message.from_user.id}")
        await message.answer("Не удалось получить картинку котика. Попробуйте позже.")

@router.message(Command("dog"))
async def cmd_dog(message: types.Message):
    logger.info(f"User {message.from_user.id} requested a dog picture")
    url = await get_random_dog()
    if url:
        await message.answer_photo(url, caption="Собачка ▼・ᴥ・▼ ")
        logger.debug(f"Dog picture sent to user {message.from_user.id}")
        record_command(message.from_user.id, "/dog")
    else:
        logger.error(f"Failed to fetch dog picture for user {message.from_user.id}")
        await message.answer("Не удалось получить картинку собачки. Попробуйте позже.")