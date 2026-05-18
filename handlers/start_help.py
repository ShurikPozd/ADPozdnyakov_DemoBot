from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import main_kb


router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Здравствуйте! Это демонстрационный бот А.Д. Позднякова.\n"
        "Доступные команды:\n"
        "/weather - погода\n"
        "/currency - конвертер валют\n"
        "/anime - распознать аниме по скриншоту\n"
        "/help - список команд",
        reply_markup=main_kb
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Диалог отменён.", reply_markup=main_kb)