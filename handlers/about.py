"""Обработчик команды /about – информация о боте."""


from aiogram import Router, types
from aiogram.filters import Command
import logging
from handlers.stats import get_stats

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("about"))
async def cmd_about(message: types.Message) -> None:
    """Отправляет информацию о боте: версия, технологии, статистика."""
    stats = get_stats()
    text = (
        "Демонстрационный бот А.Д. Позднякова\n\n"
        "Технологии:\n"
        "- Python 3.11, aiogram 3, aiohttp\n"
        "- SQLite (статистика), Flask (healthcheck)\n"
        "- Docker, GitHub Actions (CI/CD)\n\n"
        f"Статистика:\n"
        f"- Пользователей: {stats['total_users']}\n"
        f"- Выполнено команд: {stats['total_commands']}\n\n"
        "Команды: /weather, /currency, /anime, /translate, /shorten, /quote,\n"
        "/dice, /coin, /guess, /cat, /dog, /joke, /fact, /qr, /stats, /about, /cancel, /help\n\n"
        "Исходный код: [GitHub](https://github.com/ShurikPozd/ADPozdnyakov_DemoBot)\n"
        "По всем вопросам: @ShurikPozd"
    )
    await message.answer(text, disable_web_page_preview=True)