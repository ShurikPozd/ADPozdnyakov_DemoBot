import asyncio
import logging
import logger_config
from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent
from config import TOKEN
from handlers import start_help, weather, currency, anime, translate, shorten, quote, games, animals, jokes_facts, qr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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

@dp.error()
async def error_handler(event: ErrorEvent):
    logger.error(f"Unhandled exception: {event.exception}", exc_info=True)
    if event.update.message:
        await event.update.message.answer("Произошла внутренняя ошибка. Администратор уже уведомлён.")

async def main():
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception("Необработанная ошибка: %s", e, exc_info=True)