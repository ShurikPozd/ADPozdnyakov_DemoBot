"""Обработчики команд /start, /help и /cancel.

Регистрирует пользователя при /start, выводит описание бота,
отменяет активные диалоги (FSM).
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import main_kb
import logging
from handlers.stats import record_user

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    """Обрабатывает команду /start.

    Записывает пользователя в статистику, отправляет приветствие с клавиатурой.

    Args:
        message: Входящее сообщение.
    """
    record_user(message.from_user.id)
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        "Здравствуйте!\n"
        "Это демонстрационный бот А.Д. Позднякова.\n\n"
        "Доступные команды:\n\n"
        "/weather - узнать погоду\n"
        "/currency - конвертировать валюту\n"
        "/translate - перевести текст\n"
        "/anime - распознать аниме по скриншоту\n"
        "/shorten - сократить ссылку\n"
        "/qr - превратить текст/ссылку в QR-код\n"
        "/dice - бросить кости\n"
        "/coin - подбросить монету\n"
        "/guess - игра \"угадай число\"\n"
        "/quote - случайная цитата\n"
        "/cat - случайный котик\n"
        "/dog - случайная собачка\n"
        "/fact - случайный факт\n"
        "/joke - случайная шутка\n"
        "/stats - статистика бота\n"
        "/cancel - отменить диалог\n\n"
        "/help - список команд\n\n"
        "/about - информация о боте",
        reply_markup=main_kb
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    """Обрабатывает команду /help – то же самое, что /start."""
    await cmd_start(message)


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    """Отменяет любой активный диалог FSM.

    Сбрасывает состояние и уведомляет пользователя.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM, который нужно очистить.
    """
    current_state = await state.get_state()
    if current_state is None:
        logger.debug(
            f"Пользователь {message.from_user.id} использовал /cancel, но ни один из контекстов FSM не был активен"
        )
    await state.clear()
    logger.info(
        f"Пользователь {message.from_user.id} отменил активный контекст: {current_state}"
    )
    await message.answer("Диалог отменён.", reply_markup=main_kb)
