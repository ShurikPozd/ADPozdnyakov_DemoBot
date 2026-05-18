from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.trace_api import search_anime
from utils.formatters import format_time

router = Router()

class AnimeStates(StatesGroup):
    waiting_for_photo = State()

@router.message(Command("anime"))
async def anime_start(message: types.Message, state: FSMContext):
    await state.set_state(AnimeStates.waiting_for_photo)
    await message.answer("Отправьте скриншот из аниме, попробую распознать.")

@router.message(AnimeStates.waiting_for_photo)
async def process_anime_photo(message: types.Message, state: FSMContext, bot: Bot):
    if not message.photo:
        await message.answer("Отправьте изображение.")
        return

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)

    best = await search_anime(file_bytes)
    if not best:
        await message.answer("Не удалось распознать. Попробуйте другой скриншот.")
        await state.clear()
        return

    similarity = best["similarity"] * 100
    # Чистое название (можно оставить как есть, позже улучшить)
    title = best.get("filename") or best.get("anime") or best.get("title") or "Неизвестное аниме"
    episode = best.get("episode")
    from_time = best.get("from")
    to_time = best.get("to")
    time_str = f"{format_time(from_time)} – {format_time(to_time)}" if from_time and to_time else "неизвестно"

    answer = (
        f"Название: {title}\n"
        f"Похожесть: {similarity:.2f}%\n"
        f"Эпизод: {episode if episode else 'неизвестен'}\n"
        f"Таймкод: {time_str}"
    )
    await message.answer(answer, parse_mode="Markdown")
    await state.clear()