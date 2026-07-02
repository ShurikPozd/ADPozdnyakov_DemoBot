"""Гибридный парсер валют: перевод на английский + распознавание через pycountry и словарь популярных названий."""

import re
import logging
from typing import Optional, Tuple
import pycountry

logger = logging.getLogger(__name__)

# Словарь разговорных названий валют (ВСЕ КЛЮЧИ — В НИЖНЕМ РЕГИСТРЕ)
POPULAR_NAMES = {
    # Кроны — все формы
    "crown": "DKK",
    "crowns": "DKK",
    "danish crown": "DKK",
    "danish crowns": "DKK",
    "danish krone": "DKK",
    "danish kroner": "DKK",
    "czech crown": "CZK",
    "czech crowns": "CZK",
    "czech koruna": "CZK",
    "koruna": "CZK",
    "krone": "NOK",
    "kroner": "NOK",
    "norwegian krone": "NOK",
    "swedish krona": "SEK",
    "swedish kronor": "SEK",
    # Евро
    "euro": "EUR",
    "euros": "EUR",
    # Доллары
    "buck": "USD",
    "bucks": "USD",
    "greenback": "USD",
    "aussie": "AUD",
    "loonie": "CAD",
    "kiwi": "NZD",
    "hong kong dollar": "HKD",
    "singapore dollar": "SGD",
    "dollar": "USD",
    "dollars": "USD",
    "canadian dollar": "CAD",
    "canadian dollars": "CAD",
    "us dollar": "USD",
    "us dollars": "USD",
    # Фунты
    "quid": "GBP",
    "pound sterling": "GBP",
    "pound": "GBP",
    "pounds": "GBP",
    # Рубли
    "rub": "RUB",
    "ruble": "RUB",
    "rubles": "RUB",
    "rouble": "RUB",
    "roubles": "RUB",
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
    # Европа (остальные)
    "forint": "HUF",
    "zloty": "PLN",
    "leu": "RON",
    "lei": "RON",
    "romanian leu": "RON",
    "moldovan leu": "MDL",
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
    "uzbek som": "UZS",
    "kyrgyz som": "KGS",
    "tajik somoni": "TJS",
}

# Кэш для сортировки названий по длине (для приоритета фраз)
_SORTED_NAMES = sorted(POPULAR_NAMES.keys(), key=len, reverse=True)


def match_currency_by_root(word: str, currency_names: dict) -> Optional[str]:
    """Пытается сопоставить слово с валютой по корню."""
    word_lower = word.lower()

    if word_lower in currency_names:
        return currency_names[word_lower]

    for name, code in currency_names.items():
        if name in word_lower:
            return code
        if word_lower in name:
            return code

    singular = re.sub(r"(?:es|s)$", "", word_lower)
    if singular != word_lower and singular in currency_names:
        return currency_names[singular]

    for name, code in currency_names.items():
        if name.startswith(word_lower) or word_lower.startswith(name):
            return code

    return None


def find_currencies_in_text(text: str) -> list:
    """
    Находит все валюты в тексте с приоритетом фраз над отдельными словами.
    Возвращает список (позиция, код_валюты).
    """
    text_lower = text.lower()
    found = []
    used_positions = set()

    # 1. Сначала ищем фразы (более длинные названия имеют приоритет)
    for name in _SORTED_NAMES:
        if len(name.split()) < 2:  # Пропускаем одиночные слова
            continue
        pos = text_lower.find(name)
        if pos != -1:
            # Проверяем, не перекрывается ли с уже найденным
            overlapping = False
            for used_pos, used_len in used_positions:
                if pos < used_pos + used_len and used_pos < pos + len(name):
                    overlapping = True
                    break
            if not overlapping:
                found.append((pos, POPULAR_NAMES[name]))
                used_positions.add((pos, len(name)))

    # 2. Теперь ищем одиночные слова
    word_positions = []
    for match in re.finditer(r"\b\w+\b", text_lower):
        word_positions.append((match.start(), match.group()))

    for pos, word in word_positions:
        # Проверяем, не перекрывается ли с уже найденной фразой
        overlapping = False
        for used_pos, used_len in used_positions:
            if pos < used_pos + used_len and used_pos < pos + len(word):
                overlapping = True
                break
        if overlapping:
            continue

        code = match_currency_by_root(word, POPULAR_NAMES)
        if code:
            found.append((pos, code))
            used_positions.add((pos, len(word)))

    return found


def get_currency_code(currency_name: str) -> Optional[str]:
    """Преобразует название валюты в ISO-код."""
    if not currency_name:
        return None
    name = currency_name.strip().lower()
    return match_currency_by_root(name, POPULAR_NAMES)


def extract_amount(text: str) -> Optional[float]:
    """Извлекает число из текста."""
    match = re.search(r"(\d+[.,]?\d*)", text)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


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

    text_lower = en_text.lower()

    # Находим все валюты с приоритетом фраз
    currencies_with_pos = find_currencies_in_text(text_lower)

    # Проверяем pycountry для тех, что не нашли
    for cur in pycountry.currencies:
        if cur.name:
            pos = text_lower.find(cur.name.lower())
            if pos != -1:
                # Проверяем, не перекрывается ли
                overlapping = False
                for used_pos, _ in currencies_with_pos:
                    if abs(pos - used_pos) < 20:  # Примерное расстояние
                        overlapping = True
                        break
                if not overlapping:
                    currencies_with_pos.append((pos, cur.alpha_3))
        if hasattr(cur, "alternate_names") and cur.alternate_names:
            for alt_name in cur.alternate_names:
                if alt_name:
                    pos = text_lower.find(alt_name.lower())
                    if pos != -1:
                        overlapping = False
                        for used_pos, _ in currencies_with_pos:
                            if abs(pos - used_pos) < 20:
                                overlapping = True
                                break
                        if not overlapping:
                            currencies_with_pos.append((pos, cur.alpha_3))

    # Сортируем по позиции и убираем дубликаты
    currencies_with_pos.sort(key=lambda x: x[0])
    unique = []
    seen = set()
    for pos, code in currencies_with_pos:
        if code not in seen:
            seen.add(code)
            unique.append((pos, code))

    logger.debug(f"Currencies with pos: {currencies_with_pos}")
    logger.debug(f"Unique: {unique}")

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
