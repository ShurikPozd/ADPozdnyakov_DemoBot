import random
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


router = Router()


class GuessGame(StatesGroup):
    waiting_for_number = State()


@router.message(Command("dice"))
async def cmd_dice(message: types.Message):
    value = random.randint(1,6)
    await message.answer(f"Выпало: {value}", parse_mode="Markdown")


@router.message(Command("coin"))
async def cmd_coin(message: types.Message):
    result = random.choice(["Орёл", "Решка"])
    await message.answer(f"Выпало: {result}", parse_mode="Markdown")


@router.message(Command("guess"))
async def cmd_guess_start(message: types.Message, state: FSMContext):
    number = random.randint(1,10)
    await state.update_data(target=number, attempts=0)
    await state.set_state(GuessGame.waiting_for_number)
    await message.answer("Загадано число от 1 до 10. Попробуйте угадать.")


@router.message(GuessGame.waiting_for_number)
async def process_guess(message: types.Message, state: FSMContext):
    try:
        guess = int(message.text.strip())
    except ValueError:
        await message.answer("Необходимо ввести число от 1 до 10.")
        return
    
    data = await state.get_data()
    target = data['target']
    attempts = data.get('attempts', 0) + 1

    if guess == target:
        await message.answer(f"Верно! Число {target} угадано за {attempts} попыток.")
        await state.clear()
    elif guess < target:
        await message.answer("Загаданное число больше. Попробуйте ещё раз")
        await state.update_data(attempts=attempts)
    else:
        await message.answer("Загаданное число меньше. Попробуйте ещё раз.")
        await state.update_data(attempts=attempts)