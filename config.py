import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OWM_API_KEY = os.getenv("OWM_API_KEY")

if not TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения! Бот не запустится.")
else:
    logger.debug("BOT_TOKEN загружен успешно")

if not OWM_API_KEY:
    logger.warning("OWM_API_KEY не найден. Команды погоды не будут работать.")
else:
    logger.debug("OWM_API_KEY загружен успешно")
