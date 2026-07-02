"""Обработчик команды конвертации валют (/currency)."""

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.cbr_api import get_cbr_rates
from services.currency_parser_hybrid import parse_currency_request_hybrid
from services.translate_api import translate_text
from services.currency_names import (
    POPULAR_NAMES,
)  # <-- импорт остаётся, но используется в get_currency_code
import logging
from handlers.stats import record_command
from keyboards import main_kb, get_cancel_kb
import pycountry
import aiohttp

router = Router()
logger = logging.getLogger(__name__)

# Кэш для названий валют
_currency_names_cache = None


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


async def get_currency_name(code: str) -> str:
    """Получает русское название валюты по коду из кэша."""
    if _currency_names_cache is None:
        await load_currency_names()
    return _currency_names_cache.get(code, code)


async def load_currency_names() -> None:
    """Загружает названия всех валют в кэш из pycountry."""
    global _currency_names_cache
    _currency_names_cache = {}

    await _load_from_pycountry()
    await _load_from_cbr_fallback()
    _add_russian_names()

    logger.info(f"Загружено названий валют: {len(_currency_names_cache)}")


async def _load_from_pycountry() -> None:
    """Загружает названия валют из pycountry."""
    try:
        for cur in pycountry.currencies:
            if cur.alpha_3:
                _currency_names_cache[cur.alpha_3] = cur.name
    except Exception as e:
        logger.warning(f"Не удалось загрузить названия валют из pycountry: {e}")


async def _load_from_cbr_fallback() -> None:
    """Загружает названия валют из ЦБ РФ как fallback."""
    if _currency_names_cache:
        return  # Если pycountry загрузился успешно, не перезаписываем

    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    for code, info in data["Valute"].items():
                        _currency_names_cache[code] = info["Name"]
    except Exception as e:
        logger.warning(f"Не удалось загрузить названия валют из ЦБ: {e}")


def _add_russian_names() -> None:
    """Добавляет русские названия валют."""
    RUSSIAN_NAMES = {
        "AED": "Дирхам ОАЭ",
        "AMD": "Армянский драм",
        "AUD": "Австралийский доллар",
        "AZN": "Азербайджанский манат",
        "BDT": "Бангладешская така",
        "BHD": "Бахрейнский динар",
        "BOB": "Боливийский боливиано",
        "BRL": "Бразильский реал",
        "BYN": "Белорусский рубль",
        "CAD": "Канадский доллар",
        "CHF": "Швейцарский франк",
        "CNY": "Китайский юань",
        "CUP": "Кубинское песо",
        "CZK": "Чешская крона",
        "DKK": "Датская крона",
        "DZD": "Алжирский динар",
        "EGP": "Египетский фунт",
        "ETB": "Эфиопский быр",
        "EUR": "Евро",
        "GBP": "Фунт стерлингов",
        "GEL": "Грузинский лари",
        "HKD": "Гонконгский доллар",
        "HUF": "Венгерский форинт",
        "IDR": "Индонезийская рупия",
        "INR": "Индийская рупия",
        "IRR": "Иранский риал",
        "JPY": "Японская йена",
        "KGS": "Киргизский сом",
        "KRW": "Южнокорейский вон",
        "KZT": "Казахстанский тенге",
        "MDL": "Молдавский лей",
        "MMK": "Мьянманский кьят",
        "MNT": "Монгольский тугрик",
        "NGN": "Нигерийская найра",
        "NOK": "Норвежская крона",
        "NZD": "Новозеландский доллар",
        "OMR": "Оманский риал",
        "PLN": "Польский злотый",
        "QAR": "Катарский риал",
        "RON": "Румынский лей",
        "RSD": "Сербский динар",
        "RUB": "Российский рубль",
        "SAR": "Саудовский риал",
        "SEK": "Шведская крона",
        "SGD": "Сингапурский доллар",
        "THB": "Тайский бат",
        "TJS": "Таджикский сомони",
        "TMT": "Туркменский манат",
        "TRY": "Турецкая лира",
        "UAH": "Украинская гривна",
        "USD": "Доллар США",
        "UZS": "Узбекский сум",
        "VND": "Вьетнамский донг",
        "XDR": "СДР (специальные права заимствования)",
        "ZAR": "Южноафриканский рэнд",
    }

    for code, name in RUSSIAN_NAMES.items():
        _currency_names_cache[code] = name

    logger.info(f"Загружено названий валют: {len(_currency_names_cache)}")


async def format_currencies_list(rates: dict) -> str:
    """Форматирует список валют с названиями."""
    if _currency_names_cache is None:
        await load_currency_names()

    lines = []
    for code in sorted(rates.keys()):
        name = _currency_names_cache.get(code, code)
        lines.append(f"• {code} — {name}")
    return "\n".join(lines)


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
        currencies_list = await format_currencies_list(rates)
        await message.answer(
            f"Одна из валют не поддерживается.\n\n"
            f"Доступные валюты:\n{currencies_list}"
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
        rates = await get_cbr_rates()
        if rates:
            currencies_list = await format_currencies_list(rates)
            await message.answer(
                f"Не удалось распознать валюту.\n\n"
                f"Доступные валюты:\n{currencies_list}\n\n"
                f"Введите код (например, USD, EUR, RUB):",
                reply_markup=get_cancel_kb(),
            )
        else:
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
        rates = await get_cbr_rates()
        if rates:
            currencies_list = await format_currencies_list(rates)
            await message.answer(
                f"Не удалось распознать валюту.\n\n"
                f"Доступные валюты:\n{currencies_list}\n\n"
                f"Введите код (например, USD, EUR, RUB):",
                reply_markup=get_cancel_kb(),
            )
        else:
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
        currencies_list = await format_currencies_list(rates)
        await message.answer(
            f"Одна из валют не поддерживается.\n\n"
            f"Доступные валюты:\n{currencies_list}"
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


async def get_currency_code(text: str) -> str | None:
    """Пытается преобразовать русское название в код валюты."""
    text = text.strip().lower()
    logger.debug(f"get_currency_code: input='{text}'")

    # Проверяем, является ли текст кодом валюты (только латинские буквы, 3 символа)
    if len(text) == 3 and text.isascii() and text.isalpha():
        code = text.upper()
        logger.debug(f"get_currency_code: returning code '{code}' (3-letter code)")
        return code

    # 1. СНАЧАЛА проверяем прямое совпадение в словаре (русские названия)
    from services.currency_parser_hybrid import match_currency_by_root

    if text in POPULAR_NAMES:
        code = POPULAR_NAMES[text]
        logger.debug(
            f"get_currency_code: found '{text}' directly in POPULAR_NAMES -> {code}"
        )
        return code

    # Проверяем через match_currency_by_root (для частичных совпадений)
    code = match_currency_by_root(text, POPULAR_NAMES)
    if code:
        logger.debug(
            f"get_currency_code: match_currency_by_root found '{text}' -> {code}"
        )
        return code

    # 2. Если не нашли, переводим на английский
    en_text = await translate_text(text, target_lang="en")
    if not en_text:
        logger.debug(f"get_currency_code: translation failed for '{text}'")
        return None

    logger.debug(f"get_currency_code: translated '{text}' -> '{en_text}'")

    # 3. Ищем перевод на английском в словаре
    code = match_currency_by_root(en_text, POPULAR_NAMES)
    if code:
        logger.debug(
            f"get_currency_code: found '{code}' via match_currency_by_root (en)"
        )
        return code

    # 4. Пробуем через pycountry
    code = _find_currency_in_pycountry(en_text)
    if code:
        logger.debug(f"get_currency_code: found '{code}' via pycountry")
        return code

    logger.debug(f"get_currency_code: no currency found for '{text}'")
    return None


def _find_currency_in_pycountry(en_text: str) -> str | None:
    """Ищет валюту в pycountry."""
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
