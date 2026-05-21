"""Главная точка входа Telegram-бота.

Инициализирует и запускает бота со всеми зарегистрированными обработчиками.
Настраивает глобальную обработку ошибок и корректное завершение работы.
"""


import asyncio
import logging
import logger_config
from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent
from config import TOKEN
from handlers import start_help, weather, currency, anime, translate, shorten, quote, games, animals, jokes_facts, qr, stats
from flask import Flask
import threading
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
bot = Bot(token=TOKEN)
dp = Dispatcher()

flask_app = Flask(__name__)

@flask_app.route('/')
@flask_app.route('/health')
def health():
    return "Бот живой", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    flask_app.run(host='0.0.0.0', port=port)

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
dp.include_router(stats.router)

@dp.error()
async def error_handler(event: ErrorEvent) -> None:
    """Глобальный обработчик не перехваченных исключений.

    Логирует ошибку и отправляет пользователю общее сообщение (если возможно).

    Args:
        event: Объект ErrorEvent, содержащий исключение и данные обновления.
    """
    logger.error(f"Unhandled exception: {event.exception}", exc_info=True)
    if event.update.message:
        await event.update.message.answer("Произошла внутренняя ошибка. Администратор уже уведомлён.")

async def main() -> None:
    """Запускает поллинг бота (опрос сервера Telegram)."""
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Запускаем Flask в фоновом потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception("Необработанная ошибка: %s", e, exc_info=True)