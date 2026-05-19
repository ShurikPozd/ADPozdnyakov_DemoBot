from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import main_kb
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        "Здравствуйте! Это демонстрационный бот А.Д. Позднякова.\n"
        "Доступные команды:\n"
        "/weather - узнать погоду\n"
        "/currency - конвертировать валюту\n"
        "/anime - распознать аниме по скриншоту\n"
        "/translate - перевести текст\n"
        "/shorten - сократить ссылку\n"
        "/quote - случайная цитата\n"
        "/dice - бросить кости\n"
        "/coin - подбросить монету\n"
        "/guess - угадать число\n"
        "/cat - случайный котик\n"
        "/dog - случайная собачка\n"
        "/joke - случайная шутка\n"
        "/fact - случайный факт\n"
        "/cancel - отменить диалог\n"
        "/help - список команд",
        reply_markup=main_kb
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        logger.debug(f"User {message.from_user.id} tried to cancel but no active state")
    await state.clear()
    logger.info(f"User {message.from_user.id} cancelled active state: {current_state}")
    await message.answer("Диалог отменён.", reply_markup=main_kb)