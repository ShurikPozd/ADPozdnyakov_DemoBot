import json
import random
from aiogram import Router, types
from aiogram.filters import Command
from pathlib import Path
import logging

router = Router()
logger = logging.getLogger(__name__)

def get_random_quote() -> str:
    quotes_file = Path(__file__).parent.parent / 'data' / 'quotes.json'
    try:
        with open(quotes_file, 'r', encoding='utf-8') as f:
            quotes = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load quotes.json: {e}")
        return "Не удалось загрузить цитаты. Попробуйте позже."
    
    if not quotes:
        logger.warning("Quotes list is empty")
        return "Список цитат пуст"

    q = random.choice(quotes)
    text = q['text']
    author = q['author']
    tags = ', '.join(q['tags']) if q['tags'] else ''
    result = f"{text}\n\n- {author}"
    if tags:
        result += f"\n\n Теги: {tags}"
    return result

@router.message(Command("quote"))
async def cmd_quote(message: types.Message):
    logger.info(f"User {message.from_user.id} requested a quote")
    await message.answer(get_random_quote(), parse_mode="Markdown")