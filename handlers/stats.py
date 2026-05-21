"""Модуль статистики бота: сбор пользователей и команд, команда /stats.

Использует SQLite для хранения данных. Предоставляет функции для записи пользователей и команд,
а также получения агрегированной статистики.
"""

import sqlite3
from pathlib import Path
from aiogram import Router, types
from aiogram.filters import Command
import logging
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "stats.db"


def init_db() -> None:
    """Создаёт таблицы users и commands, если они ещё не существуют."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            command TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()


def record_user(user_id: int) -> None:
    """Записывает или обновляет время последнего визита пользователя.

    Args:
        user_id: ID пользователя Telegram.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        cursor.execute(
            "UPDATE users SET last_seen = ? WHERE user_id = ?", (now, user_id)
        )
    else:
        cursor.execute(
            "INSERT INTO users (user_id, first_seen, last_seen) VALUES (?, ?, ?)",
            (user_id, now, now),
        )
    conn.commit()
    conn.close()


def record_command(user_id: int, command: str) -> None:
    """Записывает факт выполнения команды.

    Args:
        user_id: ID пользователя Telegram.
        command: Название команды (например, '/weather').
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO commands (user_id, command, timestamp) VALUES (?, ?, ?)",
        (user_id, command, now),
    )
    conn.commit()
    conn.close()


def get_stats() -> dict:
    """Возвращает общую статистику: количество пользователей, команд и топ-5 команд.

    Returns:
        dict: С ключами 'total_users', 'total_commands', 'top_commands' (список кортежей (команда, количество)).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT (*) FROM commands")
    total_commands = cursor.fetchone()[0]
    cursor.execute("""
        SELECT command, COUNT(*) as cnt FROM commands
        GROUP BY command ORDER BY cnt DESC LIMIT 5
        """)
    top_commands = cursor.fetchall()
    conn.close()
    return {
        "total_users": total_users,
        "total_commands": total_commands,
        "top_commands": top_commands,
    }


init_db()


@router.message(Command("stats"))
async def cmd_stats(message: types.Message) -> None:
    """Отправляет пользователю статистику бота."""
    stats = get_stats()
    text = (
        f"Статистика бота\n"
        f"Всего пользователей: {stats['total_users']}\n"
        f"Всего команд выполнено: {stats['total_commands']}\n"
        f"Топ команд:\n"
    )
    for cmd, cnt in stats["top_commands"]:
        text += f"{cmd} - {cnt} раз(а)\n"
    await message.answer(text)
