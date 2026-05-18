from aiogram import Router, types
from aiogram.filters import Command
from services.animals_api import get_random_cat, get_random_dog


router = Router()


@router.message(Command("cat"))
async def cmd_cat(message: types.Message):
    url = await get_random_cat()
    if url:
        await message.answer_photo(url, caption="Котик  /ᐠ - ˕ -マ")
    else:
        await message.answer("Не удалось получить картинку котика. Попробуйте позже.")


@router.message(Command("dog"))
async def cmd_dog(message: types.Message):
    url = await get_random_dog()
    if url:
        await message.answer_photo(url, caption="Собачка ▼・ᴥ・▼ ")
    else:
        await message.answer("Не удалось получить картинку собачки. Попробуйте позже.")