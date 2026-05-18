import aiohttp


async def get_random_cat() -> str | None:
    url = "https://api.thecatapi.com/v1/images/search"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[0]['url']
        except Exception:
            return None
    return None


async def get_random_dog() -> str | None:
    url = "https://dog.ceo/api/breeds/image/random"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['message']
        except Exception:
            return None
    return None