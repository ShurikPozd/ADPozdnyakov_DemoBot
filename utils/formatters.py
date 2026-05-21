"""Вспомогательные функции для форматирования значений (например, времени)."""


def format_time(seconds: float | None) -> str:
    """Преобразует секунды в формат ММ:СС.

    Args:
        seconds: Время в секундах или None.

    Returns:
        Отформатированная строка, например '01:23', или '?', если seconds is None.
    """
    if seconds is None:
        return "?"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"