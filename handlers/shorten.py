from aiogram import Router, types
from aiogram.filters import Command
from services.shorten_api import shorten_url


router = Router()


@router.message(Command("shorten"))
async def cmd_shorten(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) <2:
        await message.answer("Использование: /shorten https://длинная-ссылка.ru")
        return
    
    long_url = args[1].strip()
    # Валидация
    if not (long_url.startswith("http://") or long_url.startswith("https://")):
        await message.answer("Ссылка должна начинаться с http:// или https://")
        return
    
    short = await shorten_url(long_url)
    if short:
        await message.answer(f"Короткая ссылка: {short}")
    else:
        await message.answer("Ошибка при сокращении. Проверьте ссылку и попробуйте снова.")