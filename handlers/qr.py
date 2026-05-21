from aiogram import Router, types
from aiogram.filters import Command
from services.qr_api import generate_qr_code
import logging
from handlers.stats import record_command

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("qr"))
async def cmd_qr(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        logger.debug(f"User {message.from_user.id} used /qr without text")
        await message.answer("Использование: /qr текст_или_ссылка")
        return
    text = args[1].strip()
    if len(text) > 500:
        logger.warning(f"User {message.from_user.id} sent QR data that's too long: ({len(text)} chars)")
        await message.answer("Текст слишком длинный (макс. 500 символов).")
        return
    try:
        qr_io = await generate_qr_code(text)
        # Обёртываем BytesIO в BufferedInputFile
        photo_file = types.BufferedInputFile(qr_io.getvalue(), filename="qr.png")
        await message.answer_photo(photo_file, caption=f"QR-код для:\n{text}")
        logger.debug(f"QR code sent to user {message.from_user.id}")
        record_command(message.from_user.id, "/qr")
    except Exception as e:
        logger.exception(f"QR generation failed for user {message.from_user.id}: {e}")
        await message.answer(f"Ошибка генерации QR-кода: {e}")