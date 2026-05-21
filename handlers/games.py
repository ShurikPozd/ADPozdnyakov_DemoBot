import random
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from handlers.stats import record_command

router = Router()
logger = logging.getLogger(__name__)

class GuessGame(StatesGroup):
    waiting_for_number = State()

@router.message(Command("dice"))
async def cmd_dice(message: types.Message):
    value = random.randint(1,6)
    logger.info(f"User {message.from_user.id} rolled dice: {value}")
    await message.answer(f"Выпало: {value}")
    record_command(message.from_user.id, "/dice")

@router.message(Command("coin"))
async def cmd_coin(message: types.Message):
    result = random.choice(["Орёл", "Решка"])
    logger.info(f"User {message.from_user.id} flipped coin: {result}")
    await message.answer(f"Выпало: {result}")
    record_command(message.from_user.id, "/coin")

@router.message(Command("guess"))
async def cmd_guess_start(message: types.Message, state: FSMContext):
    number = random.randint(1,10)
    await state.update_data(target=number, attempts=0)
    await state.set_state(GuessGame.waiting_for_number)
    logger.debug(f"User {message.from_user.id} started guess game, target={number}")
    await message.answer("Загадано число от 1 до 10. Попробуйте угадать.")

@router.message(GuessGame.waiting_for_number)
async def process_guess(message: types.Message, state: FSMContext):
    try:
        guess = int(message.text.strip())
    except ValueError:
        logger.debug(f"User {message.from_user.id} sent non-number guess: {message.text}")
        await message.answer("Необходимо ввести число от 1 до 10.")
        return
    
    data = await state.get_data()
    target = data['target']
    attempts = data.get('attempts', 0) + 1
    logger.debug(f"User {message.from_user.id} guessed {guess}, target {target}, attempts {attempts}")

    if guess == target:
        await message.answer(f"Верно! Число {target} угадано за {attempts} попыток.")
        logger.info(f"User {message.from_user.id} won the guess game in {attempts} attempts")
        record_command(message.from_user.id, "/guess")
        await state.clear()
    elif guess < target:
        await message.answer("Загаданное число больше. Попробуйте ещё раз")
        await state.update_data(attempts=attempts)
    else:
        await message.answer("Загаданное число меньше. Попробуйте ещё раз.")
        await state.update_data(attempts=attempts)