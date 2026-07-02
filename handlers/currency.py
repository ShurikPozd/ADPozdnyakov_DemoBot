"""Обработчик команды конвертации валют (/currency)."""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.cbr_api import get_cbr_rates
from services.currency_parser_hybrid import parse_currency_request_hybrid
from services.translate_api import translate_text
import logging
from handlers.stats import record_command
from keyboards import main_kb, get_cancel_kb
import pycountry

router = Router()
logger = logging.getLogger(__name__)


class CurrencyStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_from_currency = State()
    waiting_for_to_currency = State()


def convert_currency(
    amount: float, from_cur: str, to_cur: str, rates: dict
) -> float | None:
    if from_cur not in rates or to_cur not in rates:
        return None
    rub_amount = amount * rates[from_cur]
    result = rub_amount / rates[to_cur]
    return round(result, 2)


async def get_currency_code(text: str) -> str | None:
    """Пытается преобразовать русское название в код валюты."""
    text = text.strip().lower()
    if len(text) == 3 and text.isalpha():
        return text.upper()

    # 1. Переводим название на английский
    en_text = await translate_text(text, target_lang="en")
    if not en_text:
        return None
    
    # 2. Ищем через match_currency_by_root из гибридного парсера
    from services.currency_parser_hybrid import match_currency_by_root, POPULAR_NAMES
    
    code = match_currency_by_root(en_text, POPULAR_NAMES)
    if code:
        return code
    
    # 3. Пробуем через pycountry
    try:
        for cur in pycountry.currencies:
            if cur.name and cur.name.lower() == en_text.lower():
                return cur.alpha_3
            if hasattr(cur, "alternate_names") and cur.alternate_names:
                for alt_name in cur.alternate_names:
                    if alt_name and alt_name.lower() == en_text.lower():
                        return cur.alpha_3
    except (KeyError, AttributeError):
        pass

    return None

async def try_parse_and_convert(message: types.Message, state: FSMContext) -> bool:
    """Пытается распарсить и конвертировать запрос."""
    text = message.text.strip()
    if not text:
        return False

    rates = await get_cbr_rates()
    if rates is None:
        await message.answer("Не удалось получить курсы валют. Попробуйте позже.")
        await state.clear()
        return True

    parsed = await parse_currency_request_hybrid(text, translate_text)
    if parsed is None:
        return False

    amount, from_cur, to_cur = parsed
    result = convert_currency(amount, from_cur, to_cur, rates)

    if result is None:
        await message.answer(
            f"Одна из валют не поддерживается. Доступны: {', '.join(rates.keys())}"
        )
        await state.clear()
        return True

    await message.answer(
        f"{amount} {from_cur} = {result} {to_cur}\n(по курсу ЦБ РФ)",
        reply_markup=main_kb,
    )
    record_command(message.from_user.id, "/currency")
    await state.clear()
    return True


@router.message(Command("currency"))
async def currency_start(message: types.Message, state: FSMContext) -> None:
    """Начинает диалог конвертации, либо сразу обрабатывает полный запрос."""
    logger.info(f"User {message.from_user.id} started currency conversion")

    text = message.text.replace("/currency", "").strip()
    if text:
        if await try_parse_and_convert(message, state):
            return
        await message.answer(
            "Не удалось распознать ваш запрос. Введите сумму вручную:",
            reply_markup=get_cancel_kb(),
        )
        await state.set_state(CurrencyStates.waiting_for_amount)
        return

    await state.set_state(CurrencyStates.waiting_for_amount)
    await message.answer(
        "Введите сумму (или сразу запрос, например: 100 долларов в евро): ",
        reply_markup=get_cancel_kb(),
    )


@router.message(CurrencyStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает ввод суммы или полный запрос."""
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Диалог отменён. Отправьте команду заново.", reply_markup=main_kb
        )
        return

    if await try_parse_and_convert(message, state):
        return

    try:
        amount = float(message.text.strip())
        await state.update_data(amount=amount)
        await state.set_state(CurrencyStates.waiting_for_from_currency)
        logger.debug(f"User {message.from_user.id} entered amount: {amount}")
        await message.answer(
            "Введите исходную валюту (например, USD, EUR, RUB) или полный запрос: ",
            reply_markup=get_cancel_kb(),
        )
    except ValueError:
        logger.warning(
            f"User {message.from_user.id} entered invalid amount: {message.text}"
        )
        await message.answer(
            "Ошибка: введите число или полный запрос (например, 100 долларов в евро).",
            reply_markup=get_cancel_kb(),
        )


@router.message(CurrencyStates.waiting_for_from_currency)
async def process_from_currency(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает ввод исходной валюты или полный запрос."""
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Диалог отменён. Отправьте команду заново.", reply_markup=main_kb
        )
        return

    if await try_parse_and_convert(message, state):
        return

    text = message.text.strip()
    code = await get_currency_code(text)
    if code is None:
        await message.answer(
            "Не удалось распознать валюту. Пожалуйста, введите код (например, USD, EUR, RUB):",
            reply_markup=get_cancel_kb(),
        )
        return

    from_cur = code
    await state.update_data(from_cur=from_cur)
    await state.set_state(CurrencyStates.waiting_for_to_currency)
    logger.debug(f"User {message.from_user.id} entered from_currency: {from_cur}")
    await message.answer(
        "Введите целевую валюту (например, USD, EUR, RUB) или полный запрос:",
        reply_markup=get_cancel_kb(),
    )


@router.message(CurrencyStates.waiting_for_to_currency)
async def process_to_currency(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает ввод целевой валюты или полный запрос."""
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Диалог отменён. Отправьте команду заново.", reply_markup=main_kb
        )
        return

    if await try_parse_and_convert(message, state):
        return

    text = message.text.strip()
    code = await get_currency_code(text)
    if code is None:
        await message.answer(
            "Не удалось распознать валюту. Пожалуйста, введите код (например, USD, EUR, RUB):",
            reply_markup=get_cancel_kb(),
        )
        return

    to_cur = code
    user_data = await state.get_data()
    amount = user_data["amount"]
    from_cur = user_data["from_cur"]
    if not amount or not from_cur:
        await message.answer("Что-то пошло не так. Начните заново: /currency")
        await state.clear()
        return

    rates = await get_cbr_rates()
    if rates is None:
        await message.answer("Не удалось получить курсы валют. Попробуйте позже.")
        await state.clear()
        return

    if from_cur not in rates or to_cur not in rates:
        await message.answer(
            f"Одна из валют не найдена. Доступны: {', '.join(rates.keys())}"
        )
        await state.clear()
        return

    result = convert_currency(amount, from_cur, to_cur, rates)
    await message.answer(
        f"{amount} {from_cur} = {result} {to_cur}\n(по курсу ЦБ РФ)",
        reply_markup=main_kb,
    )
    logger.info(
        f"User {message.from_user.id} conversion result: {amount} {from_cur} = {result} {to_cur}"
    )
    record_command(message.from_user.id, "/currency")
    await state.clear()
