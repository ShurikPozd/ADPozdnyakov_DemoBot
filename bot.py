import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import start_help, weather, currency, anime, translate, shorten, quote, games, animals, jokes_facts, qr


logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


dp.include_router(start_help.router)
dp.include_router(weather.router)
dp.include_router(currency.router)
dp.include_router(anime.router)
dp.include_router(translate.router)
dp.include_router(shorten.router)
dp.include_router(quote.router)
dp.include_router(games.router)
dp.include_router(animals.router)
dp.include_router(jokes_facts.router)
dp.include_router(qr.router)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())