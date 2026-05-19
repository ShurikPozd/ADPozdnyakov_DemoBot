import aiohttp
import logging

logger = logging.getLogger(__name__)

async def shorten_url(long_url: str) -> str | None:
    url = f"https://is.gd/create.php?format=simple&url={long_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    short = await response.text()
                    if short and not short.startswith("Error"):
                        logger.debug(f"URL shortened: {long_url} -> {short.strip()}")
                        return short.strip()
                    else:
                        logger.warning(f"is.gd returned error: {short}")
                else:
                    logger.warning(f"is.gd returned status {response.status}")
    except aiohttp.ClientError as e:
        logger.error(f"Network error shortening URL {long_url}: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in shorten_url: {e}")
    return None
