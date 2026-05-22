"""Клавиатуры для Telegram-бота.

Определяет основную клавиатуру с кнопками для быстрого доступа к командам.
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/weather"), KeyboardButton(text="/currency")],
        [KeyboardButton(text="/translate"), KeyboardButton(text="/anime")],
        [KeyboardButton(text="/shorten"), KeyboardButton(text="/qr")],
        [KeyboardButton(text="/dice"), KeyboardButton(text="/coin")],
        [KeyboardButton(text="/guess"), KeyboardButton(text="/quote")],
        [KeyboardButton(text="/cat"), KeyboardButton(text="/dog")],
        [KeyboardButton(text="/fact"), KeyboardButton(text="/joke")],
        [
            KeyboardButton(text="/stats"),
            KeyboardButton(text="/about"),
            KeyboardButton(text="/help"),
        ],
    ],
    resize_keyboard=True,
)


def get_cancel_kb():
    """Клавиатура с одной кнопкой /cancel для активного диалога."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/cancel")]], resize_keyboard=True
    )
