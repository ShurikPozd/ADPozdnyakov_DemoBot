from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/weather"), KeyboardButton(text="/currency")],
        [KeyboardButton(text="/anime"), KeyboardButton(text="/cancel")],
        [KeyboardButton(text="/translate")], [KeyboardButton(text="/shorten")],
        [KeyboardButton(text="/help")]
    ],
    resize_keyboard=True
)