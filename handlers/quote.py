import json
import random
from aiogram import Router, types
from aiogram.filters import Command
from pathlib import Path


router = Router()


def get_random_quote() -> str:
    quotes_file = Path(__file__).parent.parent / 'data' / 'quotes.json'
    with open(quotes_file, 'r', encoding='utf-8') as f:
        quotes = json.load(f)
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
    await message.answer(get_random_quote(), parse_mode="Markdown")