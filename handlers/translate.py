# handlers/translate.py
from aiogram import Router, types
from aiogram.filters import Command
from services.translate_api import translate_text


router = Router()


@router.message(Command("translate"))
async def cmd_translate(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /translate <текст для перевода на русский>")
        return

    text = args[1].strip()
    if len(text) > 500:
        await message.answer("Текст слишком длинный (макс. 500 символов).")
        return

    # Перевод на русский язык
    translated = await translate_text(text, target_lang="ru")
    if translated:
        await message.answer(f"Перевод:\n{translated}")
    else:
        await message.answer("Не удалось перевести. Попробуйте позже.")