import aiohttp


async def get_random_joke() -> str | None:
    url = "https://v2.jokeapi.dev/joke/Any?safe-mode&type=single"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if not data.get('error'):
                        return data.get('joke')
        except Exception:
            pass
    return None


async def get_random_fact() -> str | None:
    url = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('text')
        except Exception:
            pass
    return None