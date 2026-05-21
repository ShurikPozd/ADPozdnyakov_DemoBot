"""Сервис перевода текста с использованием библиотеки googletrans.

Переводит текст на указанный целевой язык (по умолчанию русский).
"""


from googletrans import Translator
import logging

logger = logging.getLogger(__name__)

async def translate_text(text: str, target_lang: str = "ru") -> str | None:
    """Переводит текст на заданный язык.

    Args:
        text: Исходный текст.
        target_lang: Код целевого языка (по умолчанию 'ru').

    Returns:
        str | None: Переведённый текст или None при ошибке.
    """
    try:
        async with Translator() as translator:
            # Библиотека сама определит исходный язык
            result = await translator.translate(text, dest=target_lang)
            logger.debug(f"Translated '{text[:30]}...' to {target_lang}")
            return result.text
    except Exception as e:
        logger.error(f"Translation error for text '{text[:50]}': {e}")
        return None