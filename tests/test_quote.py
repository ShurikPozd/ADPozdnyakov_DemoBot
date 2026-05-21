"""Unit-тесты для функции get_random_quote из handlers/quote.py."""


import json
from unittest.mock import mock_open, patch
from handlers.quote import get_random_quote

def test_get_random_quote_success():
    """Проверяет, что функция возвращает строку при нормальном файле."""
    mock_quotes = [
        {"text": "Цитата 1", "author": "Автор 1", "tags": ["тег1", "тег2"]}
    ]
    with patch("builtins.open", mock_open(read_data=json.dumps(mock_quotes))):
        with patch("random.choice", return_value=mock_quotes[0]):
            result = get_random_quote()
            assert "Цитата 1" in result
            assert "Автор 1" in result
            assert "тег1, тег2" in result

def test_get_random_quote_file_not_found():
    """Проверяет, что при отсутствии файла возвращается сообщение об ошибке."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = get_random_quote()
        assert "Не удалось загрузить цитаты" in result

def test_get_random_quote_empty_json():
    """Проверяет, что при пустом списке цитат возвращается сообщение."""
    with patch("builtins.open", mock_open(read_data=json.dumps([]))):
        result = get_random_quote()
        assert "Список цитат пуст" in result