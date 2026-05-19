from googletrans import Translator
import logging

logger = logging.getLogger(__name__)

async def translate_text(text: str, target_lang: str = "ru") -> str | None:
    try:
        async with Translator() as translator:
            # Библиотека сама определит исходный язык
            result = await translator.translate(text, dest=target_lang)
            logger.debug(f"Translated '{text[:30]}...' to {target_lang}")
            return result.text
    except Exception as e:
        logger.error(f"Translation error for text '{text[:50]}': {e}")
        return None