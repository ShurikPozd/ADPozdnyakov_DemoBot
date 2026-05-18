import aiohttp


async def search_anime(file_bytes: bytes):
    url = "https://api.trace.moe/search"
    async with aiohttp.ClientSession() as session:
        form = aiohttp.FormData()
        form.add_field('image', file_bytes, filename='anime.jpg', content_type='image/jpeg')
        async with session.post(url, data=form, timeout=15) as response:
            if response.status !=200:
                return None
            data = await response.json()
            if not data.get("result"):
                return None
            return data["result"][0] # лучшее совпадение