"""Клиент для получения курсов валют Центрального банка России (ЦБ РФ).

Предоставляет асинхронную функцию для получения курсов (база – рубль) с кэшированием на 1 час.
"""

import aiohttp
import json
import logging
import time

logger = logging.getLogger(__name__)

# Кэш: храним курсы и время последнего обновления
_cached_rates = None
_cache_time = None
CACHE_TTL = 3600  # 1 час в секундах


async def get_cbr_rates() -> dict | None:
    """Получает курсы валют от ЦБ РФ (база – RUB) с кэшированием.

    Returns:
        dict: Сопоставление кода валюты (например, 'USD') с её курсом относительно 1 единицы.
              Пример: {'RUB': 1.0, 'USD': 91.5, ...}
        None: При ошибке сети или JSON.
    """
    global _cached_rates, _cache_time
    now = time.time()

    # Если кэш есть и не устарел – возвращаем
    if (
        _cached_rates is not None
        and _cache_time is not None
        and (now - _cache_time) < CACHE_TTL
    ):
        logger.debug("Возвращаем курсы валют из кэша")
        return _cached_rates

    # Иначе загружаем новые курсы
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    rates = {"RUB": 1.0}
                    for code, info in data["Valute"].items():
                        rates[code] = info["Value"] / info["Nominal"]
                    # Сохраняем в кэш
                    _cached_rates = rates
                    _cache_time = now
                    logger.info("Курсы валют обновлены и закэшированы")
                    return rates
                else:
                    logger.warning(f"CBR API returned status {response.status}")
                    return None
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching CBR rates: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in CBR response: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error in get_cbr_rates: {e}")
        return None
