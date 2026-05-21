"""Unit-тесты для функции convert_currency из handlers/currency.py."""


from handlers.currency import convert_currency

def test_convert_currency_success():
    """Проверяет корректную конвертацию валют."""
    rates = {
        "RUB": 1.0,
        "USD": 91.5,   # 1 USD = 91.5 RUB
        "EUR": 100.0,  # 1 EUR = 100 RUB
    }

    # 100 USD в RUB
    assert convert_currency(100, "USD", "RUB", rates) == 9150.0
    # 50 EUR в USD: 50*100/91.5 ≈ 54.64
    assert convert_currency(50, "EUR", "USD", rates) == round(50 * 100.0 / 91.5, 2)

def test_convert_currency_missing_from():
    """Проверяет, что при отсутствии исходной валюты возвращается None."""
    rates = {"RUB": 1.0, "USD": 91.5}
    assert convert_currency(100, "EUR", "USD", rates) is None

def test_convert_currency_missing_to():
    """Проверяет, что при отсутствии целевой валюты возвращается None."""
    rates = {"RUB": 1.0, "USD": 91.5}
    assert convert_currency(100, "USD", "EUR", rates) is None

def test_convert_currency_empty_rates():
    """Проверяет, что при пустом словаре курсов возвращается None."""
    rates = {}
    assert convert_currency(100, "USD", "EUR", rates) is None

def test_convert_currency_rounding():
    """Проверяет округление до 2 знаков."""
    rates = {"RUB": 1.0, "USD": 91.5678}
    # 1 USD в RUB должно быть 91.57
    assert convert_currency(1, "USD", "RUB", rates) == round(91.5678, 2)