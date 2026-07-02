"""Гибридный парсер валют: перевод на английский + распознавание через pycountry и словарь популярных названий."""

import re
import logging
from typing import Optional, Tuple
import pycountry
from services.currency_names import POPULAR_NAMES

logger = logging.getLogger(__name__)


# Кэш для сортировки названий по длине (для приоритета фраз)
_SORTED_NAMES = sorted(POPULAR_NAMES.keys(), key=len, reverse=True)


def _check_explicit_currencies(word_lower: str) -> Optional[str]:
    """Проверяет явные названия валют."""
    if word_lower in ["euro", "euros", "евро"]:
        return "EUR"
    if word_lower in ["бат", "baht", "bat", "bath"]:
        return "THB"
    if word_lower in ["доллар", "dollar", "dollars", "usd"]:
        return "USD"
    if word_lower in ["рубль", "ruble", "rubles", "rub"]:
        return "RUB"
    return None


def _check_currency_in_dict(word_lower: str, currency_names: dict) -> Optional[str]:
    """Проверяет вхождение в словарь."""
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


def match_currency_by_root(word: str, currency_names: dict) -> Optional[str]:
    """Пытается сопоставить слово с валютой по корню."""
    word_lower = word.lower()

    # Игнорируем короткие слова (предлоги, союзы, числа)
    if len(word_lower) < 3:
        return None

    code = _check_explicit_currencies(word_lower)
    if code:
        return code

    return _check_currency_in_dict(word_lower, currency_names)


def _find_phrases(text_lower: str, used_positions: set) -> list:
    """Находит фразы из 2+ слов в тексте."""
    found = []
    for name in _SORTED_NAMES:
        if len(name.split()) < 2:
            continue
        pos = text_lower.find(name)
        if pos != -1:
            overlapping = False
            for used_pos, used_len in used_positions:
                if pos < used_pos + used_len and used_pos < pos + len(name):
                    overlapping = True
                    break
            if not overlapping:
                found.append((pos, POPULAR_NAMES[name]))
                used_positions.add((pos, len(name)))
    return found


def _find_single_words(text_lower: str, used_positions: set) -> list:
    """Находит одиночные слова в тексте."""
    found = []
    word_positions = []
    for match in re.finditer(r"\b\w+\b", text_lower):
        word_positions.append((match.start(), match.group()))

    logger.debug(f"_find_single_words: words={word_positions}")

    for pos, word in word_positions:
        overlapping = False
        for used_pos, used_len in used_positions:
            if pos < used_pos + used_len and used_pos < pos + len(word):
                overlapping = True
                break
        if overlapping:
            continue

        code = match_currency_by_root(word, POPULAR_NAMES)
        logger.debug(f"_find_single_words: word='{word}', code={code}")
        if code:
            found.append((pos, code))
            used_positions.add((pos, len(word)))
    return found


def find_currencies_in_text(text: str) -> list:
    """
    Находит все валюты в тексте с приоритетом фраз над отдельными словами.
    Возвращает список (позиция, код_валюты).
    """
    text_lower = text.lower()
    used_positions = set()

    logger.debug(f"find_currencies_in_text: text='{text_lower}'")

    found = _find_phrases(text_lower, used_positions)
    found.extend(_find_single_words(text_lower, used_positions))

    logger.debug(f"find_currencies_in_text: found={found}")

    return found


def _check_single_currency(
    cur, text_lower: str, currencies_with_pos: list, pos: int
) -> bool:
    """Проверяет, не перекрывается ли валюта с уже найденными."""
    for used_pos, _ in currencies_with_pos:
        if abs(pos - used_pos) < 20:
            return True
    return False


def _check_pycountry_currencies(text_lower: str, currencies_with_pos: list) -> list:
    """Проверяет pycountry для валют, которые не нашли."""
    for cur in pycountry.currencies:
        if cur.name:
            pos = text_lower.find(cur.name.lower())
            if pos != -1 and not _check_single_currency(
                cur, text_lower, currencies_with_pos, pos
            ):
                currencies_with_pos.append((pos, cur.alpha_3))
        if hasattr(cur, "alternate_names") and cur.alternate_names:
            for alt_name in cur.alternate_names:
                if alt_name:
                    pos = text_lower.find(alt_name.lower())
                    if pos != -1 and not _check_single_currency(
                        cur, text_lower, currencies_with_pos, pos
                    ):
                        currencies_with_pos.append((pos, cur.alpha_3))
    return currencies_with_pos


def _get_unique_currencies(currencies_with_pos: list) -> list:
    """Сортирует и убирает дубликаты валют."""
    currencies_with_pos.sort(key=lambda x: x[0])
    unique = []
    seen = set()
    for pos, code in currencies_with_pos:
        if code not in seen:
            seen.add(code)
            unique.append((pos, code))
    return unique


def _determine_from_to(unique: list, text_lower: str) -> Tuple[str, str]:
    """Определяет исходную и целевую валюты."""
    from_currency = unique[0][1]
    to_currency = unique[1][1]

    match = re.search(r"(?:in|to|into)\s+(\w+)", text_lower)
    if match:
        target_word = match.group(1)
        target_pos = text_lower.find(target_word)
        from_pos = unique[0][0]
        if target_pos < from_pos:
            from_currency, to_currency = to_currency, from_currency

    return from_currency, to_currency


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
    currencies_with_pos = find_currencies_in_text(text_lower)
    currencies_with_pos = _check_pycountry_currencies(text_lower, currencies_with_pos)
    unique = _get_unique_currencies(currencies_with_pos)

    if len(unique) < 2:
        logger.debug("Found less than 2 unique currencies")
        return None

    from_currency, to_currency = _determine_from_to(unique, text_lower)
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
