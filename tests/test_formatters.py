"""Unit-тесты для функции format_time из utils/formatters.py."""

from utils.formatters import format_time


def test_format_time_with_seconds():
    """Проверяет корректное преобразование секунд в MM:SS."""
    assert format_time(0) == "00:00"
    assert format_time(5) == "00:05"
    assert format_time(65) == "01:05"
    assert format_time(3661) == "61:01"
    assert format_time(3599) == "59:59"


def test_format_time_with_none():
    """Проверяет, что при None возвращается '?'."""
    assert format_time(None) == "?"


def test_format_time_with_float():
    """Проверяет работу с числами с плавающей точкой."""
    assert format_time(90.5) == "01:30"
    assert format_time(59.9) == "00:59"
