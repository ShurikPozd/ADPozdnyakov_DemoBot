"""Сервис для получения случайных изображений животных.

Использует TheCatAPI (https://thecatapi.com) для котиков
и Dog API (https://dog.ceo) для собачек.
"""

import aiohttp
import logging

logger = logging.getLogger(__name__)


async def get_random_cat() -> str | None:
    """Возвращает URL случайного изображения кота.

    Returns:
        str | None: URL картинки или None при ошибке/отсутствии результата.
    """
    url = "https://api.thecatapi.com/v1/images/search"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and isinstance(data, list) and "url" in data[0]:
                        url_cat = data[0]["url"]
                        logger.debug("Cat picture URL fetched")
                        return url_cat
                    else:
                        logger.warning("Unexpected cat API response structure")
                else:
                    logger.warning(f"Cat API returned status {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching cat picture: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error in get_random_cat: {e}")
        return None


async def get_random_dog() -> str | None:
    """Возвращает URL случайного изображения собаки.

    Returns:
        str | None: URL картинки или None при ошибке/отсутствии результата.
    """
    url = "https://dog.ceo/api/breeds/image/random"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success" and "message" in data:
                        url_dog = data["message"]
                        logger.debug("Dog picture URL fetched")
                        return url_dog
                    else:
                        logger.warning(
                            f"Dog API returned error status: {data.get('status')}"
                        )
                else:
                    logger.warning(f"Dog API returned status {response.status}")
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching dog picture: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in get_random_dog: {e}")
    return None
