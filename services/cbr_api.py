import aiohttp
import json
import logging

logger = logging.getLogger(__name__)   

async def get_cbr_rates():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    data = json.loads(text)
                    rates = {'RUB': 1.0}
                    for code, info in data['Valute'].items():
                        rates[code] = info['Value'] / info['Nominal']
                    logger.debug("CBR rates fetched successfully")
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
