"""Клиент для получения курсов валют Центрального банка России (ЦБ РФ)."""

import aiohttp
import json
import logging
import time
from natasha import Segmenter, MorphVocab, NewsMorphTagger, NewsEmbedding, Doc

logger = logging.getLogger(__name__)

_cached_rates = None
_cached_names = None
_cache_time = None
CACHE_TTL = 3600

# Синонимы для валют (приводим к единому виду перед лемматизацией)
SYNONYMS = {
    "йена": "иена", # японская йена → иена (как в ЦБ)
    "йен": "иен",
    "йены": "иены",
    "йенах": "иенах",
    "тенге": "тенге",
    "бат": "бат",
    "фунт": "фунт",
    "евро": "евро",
    "доллар": "доллар",
    "рубль": "рубль",
}

# Инициализация Natasha
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)

def normalize_currency_name(word: str) -> str:
    """Приводит название валюты к форме, используемой в ЦБ."""
    word_lower = word.lower()
    return SYNONYMS.get(word_lower, word_lower)

def lemmatize_word(word: str) -> str:
    """Лемматизация одного слова через Natasha."""
    doc = Doc(word)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    for token in doc.tokens:
        token.lemmatize(morph_vocab)
        if token.lemma:
            return token.lemma
    return word.lower()

def lemmatize_phrase(phrase: str) -> str:
    """Лемматизация всей фразы (соединяем леммы через пробел)."""
    doc = Doc(phrase)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    lemmas = []
    for token in doc.tokens:
        token.lemmatize(morph_vocab)
        lemmas.append(token.lemma if token.lemma else token.text.lower())
    return ' '.join(lemmas)

async def get_cbr_rates():
    global _cached_rates, _cached_names, _cache_time
    now = time.time()

    if (_cached_rates is not None and _cache_time is not None
            and (now - _cache_time) < CACHE_TTL):
        return _cached_rates, _cached_names

    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    rates = {"RUB": 1.0}
                    names = {}

                    # Добавляем рубль вручную
                    rub_lemmas = lemmatize_phrase("рубль")
                    names[rub_lemmas] = "RUB"

                    for code, info in data["Valute"].items():
                        rates[code] = info["Value"] / info["Nominal"]
                        raw_name = info["Name"].strip().lower()
                        
                        # Нормализуем название перед лемматизацией
                        normalized_parts = [normalize_currency_name(w) for w in raw_name.split()]
                        normalized_name = ' '.join(normalized_parts)
                        
                        # Лемматизируем нормализованное полное название
                        lemmatized_full = lemmatize_phrase(normalized_name)
                        names[lemmatized_full] = code
                        
                        # Лемматизируем каждое слово отдельно
                        for word in normalized_parts:
                            lemma = lemmatize_word(word)
                            if lemma not in names:
                                names[lemma] = code
                        
                        # Также добавляем последнее слово как отдельную лемму
                        if normalized_parts:
                            last_lemma = lemmatize_word(normalized_parts[-1])
                            if last_lemma not in names:
                                names[last_lemma] = code

                    _cached_rates = rates
                    _cached_names = names
                    _cache_time = now
                    logger.info(f"Курсы валют обновлены. Загружено {len(names)} лемм")
                    return rates, names
                else:
                    logger.warning(f"CBR API returned status {response.status}")
                    return None, None
    except Exception as e:
        logger.exception(f"Error fetching CBR rates: {e}")
        return None, None