import aiohttp
import logging

logger = logging.getLogger(__name__)

async def search_anime(file_bytes: bytes):
    url = "https://api.trace.moe/search"
    try:
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field('image', file_bytes, filename='anime.jpg', content_type='image/jpeg')
            async with session.post(url, data=form, timeout=15) as response:
                if response.status !=200:
                    logger.warning(f"Trace.moe API returned status {response.status}")
                    return None
                data = await response.json()
                if not data.get("result"):
                    logger.info("No result from trace.moe for the image")
                    return None
                logger.debug("Trace.moe found a match")
                return data["result"][0] # лучшее совпадение
    except aiohttp.ClientError as e:
        logger.error(f"Network error in trace.moe request: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error in search_anime: {e}")
        return None
