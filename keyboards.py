from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/weather"), KeyboardButton(text="/currency")],
        [KeyboardButton(text="/anime"), KeyboardButton(text="/translate")],
        [KeyboardButton(text="/shorten"), KeyboardButton(text="/quote")],
        [KeyboardButton(text="/dice"), KeyboardButton(text="/coin")],
        [KeyboardButton(text="/guess"), KeyboardButton(text="/cat")],
        [KeyboardButton(text="/dog"), KeyboardButton(text="/joke")],
        [KeyboardButton(text="/fact"), KeyboardButton(text="/qr")],
        [KeyboardButton(text="/cancel"), KeyboardButton(text="/help")]
    ],
    resize_keyboard=True
)