from aiogram import Router, types
from aiogram.filters import Command
from services.jokes_facts_api import get_random_joke, get_random_fact


router = Router()


@router.message(Command("joke"))
async def cmd_joke(message: types.Message):
    joke = await get_random_joke()
    if joke:
        await message.answer(joke)
    else:
        await message.answer("Не удалось получить шутку. Попробуйте позже.")


@router.message(Command("fact"))
async def cmd_fact(message: types.Message):
    fact = await get_random_fact()
    if fact:
        await message.answer(fact)
    else:
        await message.answer("Не удалось получить интересный факт. Попробуйте позже.")