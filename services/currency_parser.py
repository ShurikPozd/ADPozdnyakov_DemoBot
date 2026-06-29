"""Парсинг запросов валют с помощью Natasha (NER + лемматизация)."""

import re
import logging
from typing import Optional, Tuple
from natasha import (
    Segmenter,
    MorphVocab,
    NewsMorphTagger,
    NewsEmbedding,
    NewsNERTagger,
    Doc,
)

logger = logging.getLogger(__name__)

segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
ner_tagger = NewsNERTagger(emb)

# Синонимы для нормализации пользовательских запросов
SYNONYMS = {
    "йена": "иена",
    "йен": "иен",
    "йены": "иены",
    "йенах": "иенах",
}


def normalize_currency_name(word: str) -> str:
    """Приводит название валюты к стандартному виду."""
    word_lower = word.lower()
    return SYNONYMS.get(word_lower, word_lower)


def lemmatize_word(word: str) -> str:
    """Лемматизация одного слова."""
    doc = Doc(word)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    for token in doc.tokens:
        token.lemmatize(morph_vocab)
        if token.lemma:
            return token.lemma
    return word.lower()


def lemmatize_text(text: str) -> str:
    """Лемматизация всего текста (сохраняем порядок слов)."""
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    lemmas = []
    for token in doc.tokens:
        token.lemmatize(morph_vocab)
        lemmas.append(token.lemma if token.lemma else token.text.lower())
    return " ".join(lemmas)


def normalize_and_lemmatize(text: str) -> str:
    """Нормализует и лемматизирует текст."""
    normalized = " ".join([normalize_currency_name(w) for w in text.split()])
    return lemmatize_text(normalized)


def extract_amount(text: str) -> Optional[float]:
    """Извлекает число из текста."""
    match = re.search(r"(\d+[.,]?\d*)", text)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def find_currency_in_text(
    text: str, currency_names: dict, exclude_code: Optional[str] = None
) -> Optional[str]:
    """Ищет валюту в тексте, сортируя названия по длине."""
    sorted_names = sorted(currency_names.keys(), key=len, reverse=True)
    for name in sorted_names:
        if name in text:
            code = currency_names[name]
            if code != exclude_code:
                return code
    return None


def find_currency_after_preposition(text: str, currency_names: dict) -> Optional[str]:
    """Ищет валюту после предлога 'в' или 'на'."""
    match = re.search(r"(?:в|на)\s+(\w+)", text)
    if match:
        word = match.group(1)
        if word in currency_names:
            return currency_names[word]
        first_w = word.split()[0] if word.split() else ""
        if first_w in currency_names:
            return currency_names[first_w]
    return None


def parse_with_natasha_ner(
    text: str, currency_names: dict
) -> Optional[Tuple[float, str, str]]:
    """Пытается распарсить текст через Natasha NER."""
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)

    money_spans = [span for span in doc.spans if span.type == "MONEY"]
    if not money_spans:
        return None

    first = money_spans[0]
    money_text = first.text
    logger.debug(f"Found MONEY: {money_text}")

    amount = extract_amount(money_text)
    if amount is None:
        return None

    # Извлекаем валюту из фрагмента
    currency_part = re.sub(r"^[\d.,\s]+", "", money_text).strip().lower()
    lemmatized_currency = normalize_and_lemmatize(currency_part)

    from_currency = None
    if lemmatized_currency in currency_names:
        from_currency = currency_names[lemmatized_currency]
    else:
        first_word = (
            lemmatized_currency.split()[0] if lemmatized_currency.split() else ""
        )
        if first_word in currency_names:
            from_currency = currency_names[first_word]

    if not from_currency:
        return None

    # Ищем целевую валюту
    remaining = text.replace(money_text, "").strip()
    lemmatized_remaining = normalize_and_lemmatize(remaining)

    to_currency = find_currency_in_text(
        lemmatized_remaining, currency_names, from_currency
    )
    if not to_currency:
        to_currency = find_currency_after_preposition(
            lemmatized_remaining, currency_names
        )

    if to_currency:
        return amount, from_currency, to_currency
    return None


def fallback_parse(text: str, currency_names: dict) -> Optional[Tuple[float, str, str]]:
    """Fallback-парсер с лемматизацией всех слов."""
    amount = extract_amount(text)
    if amount is None:
        return None

    lemmatized_text = normalize_and_lemmatize(text)
    words = lemmatized_text.split()

    # Ищем фразы и отдельные слова
    found = []
    used_positions = set()

    for i in range(len(words)):
        if i in used_positions:
            continue

        matched = False
        for j in range(i + 1, min(i + 4, len(words) + 1)):
            phrase = " ".join(words[i:j])
            if phrase in currency_names:
                found.append((i, currency_names[phrase]))
                for k in range(i, j):
                    used_positions.add(k)
                matched = True
                break

        if not matched and words[i] in currency_names:
            found.append((i, currency_names[words[i]]))
            used_positions.add(i)

    if len(found) < 2:
        return None

    # Убираем дубликаты кодов
    unique_ordered = []
    seen = set()
    for _, code in found:
        if code not in seen:
            seen.add(code)
            unique_ordered.append(code)

    if len(unique_ordered) < 2:
        return None

    return amount, unique_ordered[0], unique_ordered[-1]


def parse_currency_request(
    text: str, currency_names: dict
) -> Optional[Tuple[float, str, str]]:
    """
    Парсит текст вида "100 долларов в евро".
    Использует Natasha для NER и лемматизации.
    """
    logger.debug(f"Parsing text: {text}")

    # Попытка через Natasha NER
    result = parse_with_natasha_ner(text, currency_names)
    if result:
        return result

    # Fallback: лемматизация всех слов
    logger.debug("Using fallback parser with lemmatization")
    return fallback_parse(text, currency_names)
