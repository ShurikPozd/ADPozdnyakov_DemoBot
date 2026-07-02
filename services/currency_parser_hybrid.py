"""Гибридный парсер валют: перевод на английский + распознавание через pycountry и словарь популярных названий."""

import re
import logging
from typing import Optional, Tuple
import pycountry

logger = logging.getLogger(__name__)

# Словарь разговорных названий валют (только те, что есть в ЦБ РФ)
POPULAR_NAMES = {
    # Доллары
    "buck": "USD",
    "bucks": "USD",
    "greenback": "USD",
    "aussie": "AUD",
    "loonie": "CAD",
    "kiwi": "NZD",
    "hong kong dollar": "HKD",
    "singapore dollar": "SGD",
    # Фунты
    "quid": "GBP",
    "pound sterling": "GBP",
    # Рубли
    "rub": "RUB",
    "ruble": "RUB",
    "rouble": "RUB",
    # Азиатские
    "yuan": "CNY",
    "renminbi": "CNY",
    "yen": "JPY",
    "baht": "THB",
    "tenge": "KZT",
    "rupee": "INR",
    "rupiah": "IDR",
    "taka": "BDT",
    "kyat": "MMK",
    "riel": "KHR",
    "ringgit": "MYR",
    # Ближневосточные
    "dirham": "AED",
    "uae dirham": "AED",
    "emirati dirham": "AED",
    "shekel": "ILS",
    "new shekel": "ILS",
    "lira": "TRY",
    "rial": "IRR",
    "iranian rial": "IRR",
    "qatari riyal": "QAR",
    "saudi riyal": "SAR",
    # Африканские
    "rand": "ZAR",
    "naira": "NGN",
    "cedi": "GHS",
    "shilling": "KES",
    "kenyan shilling": "KES",
    "tanzanian shilling": "TZS",
    "ugandan shilling": "UGX",
    "kwacha": "MWK",
    "malawian kwacha": "MWK",
    "metical": "MZN",
    "pula": "BWP",
    # Латинская Америка
    "peso": "MXN",
    "cuban peso": "CUP",
    "peso cubano": "CUP",
    "argentine peso": "ARS",
    "chilean peso": "CLP",
    "colombian peso": "COP",
    "uruguayan peso": "UYU",
    "dominican peso": "DOP",
    "philippine peso": "PHP",
    "colon": "CRC",
    "colones": "CRC",
    "cordoba": "NIO",
    "guarani": "PYG",
    "boliviano": "BOB",
    "sol": "PEN",
    # Европа
    "koruna": "CZK",
    "czech koruna": "CZK",
    "crown": "CZK",
    "krone": "NOK",
    "norwegian krone": "NOK",
    "swedish krona": "SEK",
    "danish krone": "DKK",
    "forint": "HUF",
    "zloty": "PLN",
    "leu": "RON",
    "romanian leu": "RON",
    # Динары
    "dinar": "KWD",
    "kuwaiti dinar": "KWD",
    "bahraini dinar": "BHD",
    "iraqi dinar": "IQD",
    "jordanian dinar": "JOD",
    "libyan dinar": "LYD",
    "tunisian dinar": "TND",
    "algerian dinar": "DZD",
    "serbian dinar": "RSD",
    # Другие
    "real": "BRL",
    "manat": "AZN",
    "turkmenistan manat": "TMT",
    "dram": "AMD",
    "georgian lari": "GEL",
    "moldovan leu": "MDL",
    "uzbek som": "UZS",
    "kyrgyz som": "KGS",
    "tajik somoni": "TJS",
}


def get_currency_code(currency_name: str) -> Optional[str]:
    """Преобразует название валюты в ISO-код."""
    if not currency_name:
        return None
    name = currency_name.strip().lower()

    if name in POPULAR_NAMES:
        return POPULAR_NAMES[name]

    for popular_name, code in POPULAR_NAMES.items():
        if popular_name in name or name in popular_name:
            return code

    try:
        currency = pycountry.currencies.get(name=currency_name.title())
        if currency:
            return currency.alpha_3
    except (KeyError, AttributeError):
        pass

    for cur in pycountry.currencies:
        if cur.name:
            cur_name_lower = cur.name.lower()
            if name in cur_name_lower or cur_name_lower in name:
                return cur.alpha_3

    for cur in pycountry.currencies:
        if hasattr(cur, "alternate_names") and cur.alternate_names:
            for alt_name in cur.alternate_names:
                if alt_name and (alt_name.lower() == name or alt_name.lower() in name):
                    return cur.alpha_3

    return None


def extract_amount(text: str) -> Optional[float]:
    """Извлекает число из текста."""
    match = re.search(r"(\d+[.,]?\d*)", text)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def extract_currency_from_text(text: str) -> Optional[str]:
    """Извлекает валюту из текста."""
    text_lower = text.lower()

    for name, code in POPULAR_NAMES.items():
        if name in text_lower:
            return code

    for cur in pycountry.currencies:
        if cur.name and cur.name.lower() in text_lower:
            return cur.alpha_3
        if hasattr(cur, "alternate_names") and cur.alternate_names:
            for alt_name in cur.alternate_names:
                if alt_name and alt_name.lower() in text_lower:
                    return cur.alpha_3

    return None


async def parse_with_translate(
    text: str, translator_func
) -> Optional[Tuple[float, str, str]]:
    """Парсит запрос через перевод на английский."""
    en_text = await translator_func(text, target_lang="en")
    if not en_text:
        logger.debug("Translation failed")
        return None

    logger.debug(f"Translated text: {en_text}")

    amount = extract_amount(en_text)
    if amount is None:
        return None

    # Находим все валюты в тексте с их позициями
    currencies_with_pos = []
    text_lower = en_text.lower()

    for name, code in POPULAR_NAMES.items():
        pos = text_lower.find(name)
        if pos != -1:
            currencies_with_pos.append((pos, code))

    for cur in pycountry.currencies:
        if cur.name:
            pos = text_lower.find(cur.name.lower())
            if pos != -1:
                currencies_with_pos.append((pos, cur.alpha_3))
        if hasattr(cur, "alternate_names") and cur.alternate_names:
            for alt_name in cur.alternate_names:
                if alt_name:
                    pos = text_lower.find(alt_name.lower())
                    if pos != -1:
                        currencies_with_pos.append((pos, cur.alpha_3))

    # Убираем дубликаты (оставляем первое вхождение)
    unique = []
    seen = set()
    for pos, code in sorted(currencies_with_pos, key=lambda x: x[0]):
        if code not in seen:
            seen.add(code)
            unique.append((pos, code))

    if len(unique) < 2:
        logger.debug("Found less than 2 unique currencies")
        return None

    from_currency = unique[0][1]
    to_currency = unique[1][1]

    # Проверяем по предлогу
    match = re.search(r"(?:in|to|into)\s+(\w+)", text_lower)
    if match:
        target_word = match.group(1)
        target_pos = text_lower.find(target_word)
        from_pos = unique[0][0]

        # Если целевая валюта стоит раньше исходной в тексте, меняем местами
        if target_pos < from_pos:
            from_currency, to_currency = to_currency, from_currency

    return amount, from_currency, to_currency


async def parse_currency_request_hybrid(
    text: str, translator_func
) -> Optional[Tuple[float, str, str]]:
    """Гибридный парсер: перевод + распознавание через pycountry и словарь."""
    logger.debug(f"Hybrid parser: parsing '{text}'")
    try:
        return await parse_with_translate(text, translator_func)
    except Exception as e:
        logger.error(f"Hybrid parser error: {e}")
        return None