from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.trace_api import search_anime
from utils.formatters import format_time
import logging
from handlers.stats import record_command

router = Router()
logger = logging.getLogger(__name__)

class AnimeStates(StatesGroup):
    waiting_for_photo = State()

@router.message(Command("anime"))
async def anime_start(message: types.Message, state: FSMContext):
    logging.debug(f"User {message.from_user.id} started anime recognition")
    await state.set_state(AnimeStates.waiting_for_photo)
    await message.answer("Отправьте скриншот из аниме, попробую распознать.")

@router.message(AnimeStates.waiting_for_photo)
async def process_anime_photo(message: types.Message, state: FSMContext, bot: Bot):
    if not message.photo:
        logger.debug(f"User {message.from_user.id} sent message without photo")
        await message.answer("Отправьте изображение.")
        return

    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_bytes = await bot.download_file(file.file_path)
    size = file_bytes.getbuffer().nbytes
    logger.debug(f"Photo from user {message.from_user.id} downloaded, size: {size} bytes")

    best = await search_anime(file_bytes)
    if not best:
        logger.warning(f"No recognition result for user {message.from_user.id}")
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
    await message.answer(answer)
    logger.info(f"Anime recognized for user {message.from_user.id}: {title} (similarity {similarity:.2f}%)")
    record_command(message.from_user.id, "/anime")
    await state.clear()