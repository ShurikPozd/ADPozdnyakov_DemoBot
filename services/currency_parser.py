"""Парсинг запросов валют с помощью Natasha (NER + лемматизация)."""

import re
import logging
from typing import Optional, Tuple
from natasha import Segmenter, MorphVocab, NewsMorphTagger, NewsEmbedding, NewsNERTagger, Doc

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
    return ' '.join(lemmas)

def parse_currency_request(text: str, currency_names: dict) -> Optional[Tuple[float, str, str]]:
    """
    Парсит текст вида "100 долларов в евро".
    Использует Natasha для NER и лемматизации.
    """
    logger.debug(f"Parsing text: {text}")

    # ---------- Попытка через Natasha NER ----------
    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_ner(ner_tagger)

    spans_info = [(span.text, span.type) for span in doc.spans]
    logger.debug(f"NER spans: {spans_info}")

    money_spans = [span for span in doc.spans if span.type == "MONEY"]
    if money_spans:
        first = money_spans[0]
        money_text = first.text
        logger.debug(f"Found MONEY: {money_text}")

        amount_match = re.search(r'(\d+[.,]?\d*)', money_text)
        if not amount_match:
            logger.debug("Could not extract number from MONEY, fallback")
        else:
            amount = float(amount_match.group(1).replace(',', '.'))

            # Лемматизируем часть с валютой
            currency_part = re.sub(r'^[\d.,\s]+', '', money_text).strip().lower()
            normalized = ' '.join([normalize_currency_name(w) for w in currency_part.split()])
            lemmatized_currency = lemmatize_text(normalized)
            
            from_currency = None
            # Ищем в словаре по лемме
            if lemmatized_currency in currency_names:
                from_currency = currency_names[lemmatized_currency]
            else:
                # Пробуем по первому слову
                first_word = lemmatized_currency.split()[0] if lemmatized_currency.split() else ""
                if first_word in currency_names:
                    from_currency = currency_names[first_word]
            
            if not from_currency:
                logger.debug(f"Currency not found: {lemmatized_currency}")
            else:
                # Ищем целевую валюту в оставшемся тексте
                remaining = text.replace(money_text, '').strip()
                normalized_remaining = ' '.join([normalize_currency_name(w) for w in remaining.split()])
                lemmatized_remaining = lemmatize_text(normalized_remaining)
                
                to_currency = None
                # Сортируем названия по длине (чтобы сначала проверять более длинные)
                sorted_names = sorted(currency_names.keys(), key=len, reverse=True)
                for name in sorted_names:
                    if name in lemmatized_remaining and currency_names[name] != from_currency:
                        to_currency = currency_names[name]
                        break
                
                if not to_currency:
                    # Пробуем найти после предлога "в" или "на"
                    match = re.search(r'(?:в|на)\s+(\w+)', lemmatized_remaining)
                    if match:
                        word = match.group(1)
                        if word in currency_names:
                            to_currency = currency_names[word]
                        else:
                            first_w = word.split()[0] if word.split() else ""
                            if first_w in currency_names:
                                to_currency = currency_names[first_w]
                
                if to_currency:
                    return amount, from_currency, to_currency
                else:
                    logger.debug("Could not find target currency via Natasha, fallback")

    # ---------- Fallback: лемматизация всех слов ----------
    logger.debug("Using fallback parser with lemmatization")

    amount_match = re.search(r'(\d+[.,]?\d*)', text)
    if not amount_match:
        logger.debug("No number found")
        return None
    amount = float(amount_match.group(1).replace(',', '.'))

    # Нормализуем и лемматизируем весь текст
    normalized_text = ' '.join([normalize_currency_name(w) for w in text.split()])
    lemmatized_text = lemmatize_text(normalized_text)

    # Ищем все леммы и фразы, которые есть в словаре
    found = []  # (позиция, код_валюты)
    words = lemmatized_text.split()

    # Сначала ищем более длинные совпадения (фразы из 2-3 слов)
    used_positions = set()
    for i in range(len(words)):
        if i in used_positions:
            continue
        # Проверяем фразы из 2-3 слов
        matched = False
        for j in range(i+1, min(i+4, len(words)+1)):
            phrase = ' '.join(words[i:j])
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
        logger.debug(f"Fallback: found only {len(set(c for _, c in found))} unique currencies")
        return None

    # Убираем дубликаты кодов (оставляем первое вхождение)
    unique_ordered = []
    seen = set()
    for _, code in found:
        if code not in seen:
            seen.add(code)
            unique_ordered.append(code)

    if len(unique_ordered) < 2:
        logger.debug("Fallback: less than 2 unique currencies")
        return None

    from_currency = unique_ordered[0]
    to_currency = unique_ordered[-1]

    return amount, from_currency, to_currency