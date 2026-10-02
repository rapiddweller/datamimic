from types import SimpleNamespace

import pytest

from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator


@pytest.fixture
def transaction_generator(monkeypatch: pytest.MonkeyPatch) -> TransactionGenerator:
    generator = TransactionGenerator()
    monkeypatch.setattr(generator, "get_transaction_type", lambda: {"type": "purchase", "direction": "debit"})
    monkeypatch.setattr(generator, "get_merchant_category", lambda: "retail")
    monkeypatch.setattr(generator, "get_merchant_name", lambda category: "shop")
    monkeypatch.setattr(generator, "generate_amount", lambda category, transaction_type: 12.5)
    monkeypatch.setattr(generator, "get_status", lambda: "completed")
    monkeypatch.setattr(generator, "get_channel", lambda: "online")
    monkeypatch.setattr(generator, "get_location", lambda: "Paris")
    monkeypatch.setattr(generator, "get_reference_number", lambda: "reference")
    monkeypatch.setattr(generator, "generate_description", lambda transaction_type, merchant_name: "purchase")
    return generator


def test_non_account_object_uses_generated_currency(
    transaction_generator: TransactionGenerator, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def get_currency() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"code": "AUD", "symbol": "$"}

    monkeypatch.setattr(transaction_generator, "get_currency", get_currency)

    data = transaction_generator.generate_transaction_data(object())

    assert data["currency_code"] == "AUD"
    assert calls == 1


def test_account_with_currency_uses_its_currency(
    transaction_generator: TransactionGenerator, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        transaction_generator,
        "get_currency",
        lambda: pytest.fail("account currency should be used"),
    )

    data = transaction_generator.generate_transaction_data(SimpleNamespace(currency="EUR"))

    assert data["currency_code"] == "EUR"
    assert data["currency_symbol"] == "€"


def test_falsey_account_with_currency_uses_generated_currency(
    transaction_generator: TransactionGenerator, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FalseyCurrencyAccount:
        currency = "EUR"

        def __bool__(self) -> bool:
            return False

    monkeypatch.setattr(
        transaction_generator,
        "get_currency",
        lambda: {"code": "AUD", "symbol": "$"},
    )

    data = transaction_generator.generate_transaction_data(FalseyCurrencyAccount())

    assert data["currency_code"] == "AUD"
