"""Обработчик команды конвертации валют (/currency).

Использует курсы ЦБ РФ (с кэшированием) и FSM для последовательного ввода суммы,
исходной и целевой валюты.
"""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.cbr_api import get_cbr_rates
from services.currency_parser import parse_currency_request
import logging
from handlers.stats import record_command
from keyboards import main_kb, get_cancel_kb

router = Router()
logger = logging.getLogger(__name__)


class CurrencyStates(StatesGroup):
    """Состояния FSM для конвертации валют."""

    waiting_for_amount = State()
    waiting_for_from_currency = State()
    waiting_for_to_currency = State()


def convert_currency(
    amount: float, from_cur: str, to_cur: str, rates: dict
) -> float | None:
    """Конвертирует сумму из одной валюты в другую на основе курсов.

    Args:
        amount: Сумма в исходной валюте.
        from_cur: Код исходной валюты (например, 'USD').
        to_cur: Код целевой валюты (например, 'EUR').
        rates: Словарь курсов (база — рубль).

    Returns:
        float: Сконвертированная сумма, округлённая до 2 знаков, или None, если валюта не найдена.
    """
    if from_cur not in rates or to_cur not in rates:
        return None
    rub_amount = amount * rates[from_cur]
    result = rub_amount / rates[to_cur]
    return round(result, 2)

async def get_currency_code(text: str) -> str | None:
    """Пытается преобразовать русское название в код валюты (USD, EUR и т.д.)."""
    text = text.strip().lower()
    # Если это уже код из 3 букв, возвращаем его в верхнем регистре
    if len(text) == 3 and text.isalpha():
        return text.upper()
    # Иначе ищем в словаре названий
    rates, names = await get_cbr_rates()
    if names is None:
        return None
    # Прямой поиск
    if text in names:
        return names[text]
    # Поиск по первому слову (для "доллар сша" -> "доллар")
    first_word = text.split()[0]
    if first_word in names:
        return names[first_word]
    return None

async def try_parse_and_convert(message: types.Message, state: FSMContext) -> bool:
    """
    Пытается распарсить сообщение как полный запрос.
    Если успешно — конвертирует, отвечает и очищает состояние.
    Возвращает True, если запрос обработан, иначе False.
    """
    text = message.text.strip()
    if not text:
        return False
    
    rates, names = await get_cbr_rates()
    if rates is None:
        await message.answer("Не удалось получить курсы валют. Попробуйте позже.")
        await state.clear()
        return True # считаем, что обработали (с ошибкой)
    
    parsed = parse_currency_request(text, names)
    if parsed is None:
        return False
    
    amount, from_cur, to_cur = parsed
    result = convert_currency(amount, from_cur, to_cur, rates)
    if result is None:
        await message.answer(f"Одна из валют не поддерживается. Доступны: {', '.join(rates.keys())}")
        await state.clear()
        return True
    
    await message.answer(f"{amount} {from_cur} = {result} {to_cur}\n(по курсу ЦБ РФ)", reply_markup=main_kb)
    record_command(message.from_user.id, "/currency")
    await state.clear()
    return True

@router.message(Command("currency"))
async def currency_start(message: types.Message, state: FSMContext) -> None:
    """Начинает диалог конвертации, либо сразу обрабатывает полный запрос.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    logger.info(f"User {message.from_user.id} started currency conversion")

    # Проверяем, есть ли текст после команды
    text = message.text.replace("/currency", "").strip()
    if text:
        # Пытаемся обработать как полный запрос
        if await try_parse_and_convert(message, state):
            return
        # Если не удалось распарсить, можно продолжить FSM или сообщить
        # Пока просто запускаем FSM
        await message.answer("Не удалось распознать ваш запрос. Введите сумму вручную:", reply_markup=get_cancel_kb())
        await state.set_state(CurrencyStates.waiting_for_amount)
        return

    # Если текста нет — запускаем FSM
    await state.set_state(CurrencyStates.waiting_for_amount)
    await message.answer("Введите сумму (или сразу запрос, например: 100 долларов в евро): ", reply_markup=get_cancel_kb())


@router.message(CurrencyStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает ввод суммы, переходит к запросу исходной валюты; или же обрабатывает полный запрос.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Диалог отменён. Отправьте команду заново.", reply_markup=main_kb
        )
        return
    
    # Пробуем распарсить полный запрос
    if await try_parse_and_convert(message, state):
        return

    # Если не распарсилось — пробуем как число
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
            "Ошибка: введите число или полный запрос (например, 100 долларов в евро).", reply_markup=get_cancel_kb()
        )


@router.message(CurrencyStates.waiting_for_from_currency)
async def process_from_currency(message: types.Message, state: FSMContext) -> None:
    """Обрабатывает ввод исходной валюты или полный запрос; переходит к запросу целевой валюты.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM.
    """
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Диалог отменён. Отправьте команду заново.", reply_markup=main_kb
        )
        return
    
    # Пробуем распарсить полный запрос
    if await try_parse_and_convert(message, state):
        return

    # Если нет — пытаемся распознать название валюты
    text = message.text.strip()
    code = await get_currency_code(text)
    if code is None:
        # Не удалось распознать - просим ввести код
        await message.answer("Не удалось распознать валюту. Пожалуйста, введите код (например, USD, EUR, RUB):", reply_markup=get_cancel_kb())
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
    """Обрабатывает ввод целевой валюты или полный запрос; выполняет конвертацию и отправляет результат.

    Args:
        message: Входящее сообщение.
        state: Контекст FSM (очищается после ответа).
    """
    if message.text.startswith("/"):
        await state.clear()
        await message.answer(
            "Диалог отменён. Отправьте команду заново.", reply_markup=main_kb
        )
        return
    
     # Пробуем распарсить полный запрос
    if await try_parse_and_convert(message, state):
        return

    # Если нет — распознаём название валюты
    text = message.text.strip()
    code = await get_currency_code(text)
    if code is None:
        await message.answer("Не удалось распознать валюту. Пожалуйста, введите код (например, USD, EUR, RUB):", reply_markup=get_cancel_kb())
        return
    
    to_cur = code
    user_data = await state.get_data()
    amount = user_data["amount"]
    from_cur = user_data["from_cur"]
    if not amount or not from_cur:
        await message.answer("Что-то пошло не так. Начните заново: /currency")
        await state.clear()
        return

    logger.debug(
        f"User {message.from_user.id} converting {amount} {from_cur} -> {to_cur}"
    )

    rates, _ = await get_cbr_rates()
    if rates is None:
        logger.error(f"User {message.from_user.id}: failed to get CBR rates")
        await message.answer("Не удалось получить курсы валют. Попробуйте позже.")
        await state.clear()
        return

    if from_cur not in rates or to_cur not in rates:
        await message.answer(f"Одна из валют не найдена. Доступны: {', '.join(rates.keys())}")
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
