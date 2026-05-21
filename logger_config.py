"""Настройка системы логирования для бота.

Создаёт папку logs/, настраивает корневой логгер с выводом в консоль и файл (ротация 10 МБ, 5 бэкапов).
"""


import logging
import logging.handlers
from pathlib import Path

# Создаём папку для логов
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Настройка корневого логгера (будет использоваться aiogram и всеми модулями)
def setup_root_logger() -> logging.Logger:
    """Настраивает корневой логгер: консоль + файл с ротацией.

    Returns:
        logging.Logger: Настроенный корневой логгер.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Формат
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Консольный handler (для aiogram и наших логов)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Файловый handler с ротацией (10 МБ на файл, храним 5 файлов)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "bot.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger

# Вызываем настройку при импорте
setup_root_logger()
logging.info("Система логирования инициализирована (консоль + файл с ротацией)")