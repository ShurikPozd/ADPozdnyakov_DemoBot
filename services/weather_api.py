import aiohttp
from config import OWM_API_KEY
import logging

logger = logging.getLogger(__name__)

async def get_weather(city: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang=ru"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                data = await response.json()
                if response.status == 200 and 'main' in data:
                    logger.debug(f"Weather data received for city: {city}")
                    return data
                else:
                    logger.warning(f"Weather API returned status {response.status} for city {city}, response: {data.get('message', 'no message')}")
                    return None
    except aiohttp.ClientError as e:
        logger.error(f"Network error while fetching weather for {city}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error in get_weather for {city}: {e}")
        return None