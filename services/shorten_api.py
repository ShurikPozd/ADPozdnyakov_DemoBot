import aiohttp


async def shorten_url(long_url: str) -> str | None:
    url = f"https://is.gd/create.php?format=simple&url={long_url}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    short = await response.text()
                    return short.strip()
                return None
        except Exception:
            return None