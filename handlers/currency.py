import json
import aiohttp
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.cbr_api import get_cbr_rates


router = Router()


class CurrencyStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_from_currency = State()
    waiting_for_to_currency = State()


def convert_currency(amount, from_cur, to_cur, rates):
    if from_cur not in rates or to_cur not in rates:
        return None
    rub_amount = amount * rates[from_cur]
    result = rub_amount / rates[to_cur]
    return round(result, 2)


@router.message(Command("currency"))
async def currency_start(message: types.Message, state: FSMContext):
    await state.set_state(CurrencyStates.waiting_for_amount)
    await message.answer("Введите сумму: ")


@router.message(CurrencyStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        await state.update_data(amount=amount)
        await state.set_state(CurrencyStates.waiting_for_from_currency)
        await message.answer("Введите исходную валюту (например, USD, EUR, RUB): ")
    except ValueError:
        await message.answer("Ошибка: введите число. Попробуйте ещё раз.")


@router.message(CurrencyStates.waiting_for_from_currency)
async def process_from_currency(message: types.Message, state: FSMContext):
    from_cur = message.text.strip().upper()
    await state.update_data(from_cur=from_cur)
    await state.set_state(CurrencyStates.waiting_for_to_currency)
    await message.answer("Введите целевую валюту (например, USD, EUR, RUB): ")


@router.message(CurrencyStates.waiting_for_to_currency)
async def process_to_currency(message: types.Message, state: FSMContext):
    to_cur = message.text.strip().upper()
    user_data = await state.get_data()
    amount = user_data['amount']
    from_cur = user_data['from_cur']

    rates = await get_cbr_rates()
    if rates is None:
        await message.answer("Не удалось получить курсы валют. Попробуйте позже.")
        await state.clear()
        return

    if from_cur not in rates:
        await message.answer(f"Валюта {from_cur} не найдена. Доступны: RUB, USD, EUR и др.")
        await state.clear()
        return
    if to_cur not in rates:
        await message.answer(f"Валюта {to_cur} не найдена. Доступны: RUB, USD, EUR и др.")
        await state.clear()
        return

    result = convert_currency(amount, from_cur, to_cur, rates)
    await message.answer(f"{amount} {from_cur} = {result} {to_cur}\n(по курсу ЦБ РФ)")
    await state.clear()