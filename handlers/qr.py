"""Генератор QR-кодов (/qr).

Реализует FSM: запрашивает текст/ссылку, генерирует QR-код.
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.qr_api import generate_qr_code
import logging
from handlers.stats import record_command
from keyboards import main_kb, get_cancel_kb

router = Router()
logger = logging.getLogger(__name__)


class QRStates(StatesGroup):
    waiting_for_data = State()


@router.message(Command("qr"))
async def qr_start(message: types.Message, state: FSMContext) -> None:
    """Начинает диалог генерации QR-кода, запрашивает данные."""
    logger.info(f"Пользователь {message.from_user.id} отправил команду /qr")
    await state.set_state(QRStates.waiting_for_data)
    await message.answer(
        "Отправьте текст или ссылку для генерации QR-кода.",
        reply_markup=get_cancel_kb(),
    )


@router.message(QRStates.waiting_for_data)
async def process_qr(message: types.Message, state: FSMContext) -> None:
    """Генерирует QR-код для полученных данных и отправляет изображение."""
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Диалог отменён. Отправьте команду заново.", reply_markup=main_kb
        )
        return
    data = message.text.strip()
    if not data:
        await message.answer(
            "Пожалуйста, отправьте текст или ссылку.", reply_markup=get_cancel_kb()
        )
        return

    if len(data) > 500:
        logger.warning(
            f"Пользователь {message.from_user.id} слишком длинные данные для превращения в QR: ({len(data)} символов)"
        )
        await message.answer(
            "Текст слишком длинный (макс. 500 символов).\n"
            "Попробуйте текст/ссылку короче",
            reply_markup=get_cancel_kb(),
        )
        return

    try:
        qr_io = await generate_qr_code(data)
        # Обёртываем BytesIO в BufferedInputFile
        photo_file = types.BufferedInputFile(qr_io.getvalue(), filename="qr.png")
        await message.answer_photo(
            photo_file, caption=f"QR-код для:\n{data}", reply_markup=main_kb
        )
        logger.debug(f"QR-код отправлен пользователю {message.from_user.id}")
        record_command(message.from_user.id, "/qr")
    except Exception as e:
        logger.exception(
            f"Генерация QR провалилась для пользователя {message.from_user.id}: {e}"
        )
        await message.answer(f"Ошибка генерации QR-кода: {e}", reply_markup=main_kb)

    await state.clear()
