"""Клиент для получения курсов валют Центрального банка России (ЦБ РФ)."""

import aiohttp
import json
import logging
import time

logger = logging.getLogger(__name__)

_cached_rates = None
_cache_time = None
CACHE_TTL = 3600  # 1 час


async def get_cbr_rates() -> dict | None:
    """Получает курсы валют от ЦБ РФ (база – RUB) с кэшированием."""
    global _cached_rates, _cache_time
    now = time.time()

    if (
        _cached_rates is not None
        and _cache_time is not None
        and (now - _cache_time) < CACHE_TTL
    ):
        logger.debug("Возвращаем курсы валют из кэша")
        return _cached_rates

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
                    _cached_rates = rates
                    _cache_time = now
                    logger.info(f"Курсы валют обновлены. Загружено {len(rates)} валют")
                    return rates
                else:
                    logger.warning(f"CBR API returned status {response.status}")
                    return None
    except Exception as e:
        logger.exception(f"Error fetching CBR rates: {e}")
        return None
