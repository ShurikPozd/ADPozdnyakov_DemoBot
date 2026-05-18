from googletrans import Translator


async def translate_text(text: str, target_lang: str = "ru") -> str | None:
    try:
        async with Translator() as translator:
            # Библиотека сама определит исходный язык
            result = await translator.translate(text, dest=target_lang)
            return result.text
    except Exception:
        return None