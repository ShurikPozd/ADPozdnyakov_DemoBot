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

# Приоритет валют (чем меньше число, тем выше приоритет)
CURRENCY_PRIORITY = {
    "USD": 1,   # Доллар США — самый важный
    "EUR": 2,
    "RUB": 3,
    "GBP": 4,
    "CNY": 5,
    "JPY": 6,
    # Остальные валюты получают низкий приоритет
}

def get_priority(code: str) -> int:
    """Возвращает приоритет валюты (чем меньше, тем выше)."""
    return CURRENCY_PRIORITY.get(code, 999)

# Инициализация Natasha
segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)

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

def add_currency_name(name: str, code: str, names: dict) -> None:
    """Добавляет название валюты в словарь с учётом приоритета."""
    if name not in names:
        names[name] = code
    else:
        existing_code = names[name]
        # Если текущая валюта имеет более высокий приоритет — заменяем
        if get_priority(code) < get_priority(existing_code):
            names[name] = code

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
                        
                        # Добавляем полное название
                        names[raw_name] = code
                        
                        # Разбиваем на слова и лемматизируем
                        words = raw_name.split()
                        lemmatized_words = [lemmatize_word(w) for w in words]
                        
                        # Добавляем каждую лемму с приоритетом
                        for lemma in lemmatized_words:
                            add_currency_name(lemma, code, names)
                        
                        # Добавляем фразы из 2-3 слов (для "доллар сша" и т.д.)
                        for i in range(len(lemmatized_words)):
                            for j in range(i+1, min(i+4, len(lemmatized_words)+1)):
                                phrase = ' '.join(lemmatized_words[i:j])
                                add_currency_name(phrase, code, names)

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