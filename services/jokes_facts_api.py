"""Сервис для получения случайных шуток и интересных фактов.

Использует JokeAPI (https://v2.jokeapi.dev) для шуток
и Useless Facts API (https://uselessfacts.jsph.pl) для фактов.
"""

import aiohttp
import logging

logger = logging.getLogger(__name__)


async def get_random_joke() -> str | None:
    """Возвращает случайную шутку (текст).

    Returns:
        str | None: Текст шутки или None при ошибке.
    """
    url = "https://v2.jokeapi.dev/joke/Any?safe-mode&type=single"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data.get("error"):
                        logger.debug("Joke fetched successfully")
                        return data.get("joke")
                    else:
                        logger.warning(
                            f"Joke API returned error: {data.get('message')}"
                        )
                else:
                    logger.warning(f"Joke API returned status {response.status}")
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching joke: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in get_random_joke: {e}")
    return None


async def get_random_fact() -> str | None:
    """Возвращает случайный интересный факт (текст).

    Returns:
        str | None: Текст факта или None при ошибке.
    """
    url = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    fact = data.get("text")
                    logger.debug("Fact fetched successfully")
                    return fact
                else:
                    logger.warning(f"Fact API returned status {response.status}")
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching fact: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in get_random_fact: {e}")
    return None
