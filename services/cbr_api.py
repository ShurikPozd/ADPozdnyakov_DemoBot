import aiohttp
import json


async def get_cbr_rates():
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                text = await response.text()
                data = json.loads(text)
                rates = {'RUB': 1.0}
                for code, info in data['Valute'].items():
                    rates[code] = info['Value'] / info['Nominal']
                return rates
            return None