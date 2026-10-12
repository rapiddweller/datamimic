from datetime import datetime, timezone
from random import Random

from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator
from datamimic_ce.domains.finance.models.bank_account import BankAccount
from datamimic_ce.domains.finance.models.transaction import Transaction


def _account() -> BankAccount:
    reference_now = datetime(2026, 9, 29, 10, 30, tzinfo=timezone.utc)
    return BankAccount(BankAccountGenerator(dataset="DE", rng=Random(31), reference_now=reference_now))


def _transaction(monkeypatch, account: BankAccount | None = None) -> tuple[Transaction, datetime]:
    generator = TransactionGenerator(rng=Random(17))
    generated = {
        "amount": 12.5,
        "description": "Coffee",
        "reference_number": "ref-1",
        "status": "completed",
        "currency_code": "EUR",
        "currency_symbol": "€",
        "merchant": "Cafe",
        "location": "Berlin",
        "channel": "card",
        "direction": "debit",
    }
    timestamp = datetime(2026, 9, 29, 10, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(generator, "get_merchant_category", lambda: "food")
    monkeypatch.setattr(generator, "get_transaction_type", lambda: {"type": "purchase", "direction": "debit"})
    monkeypatch.setattr(generator, "generate_transaction_data", lambda _account: generated)
    monkeypatch.setattr(generator, "generate_transaction_date", lambda: timestamp)
    transaction = Transaction(generator, account)
    transaction.field_cache.update(
        {
            "transaction_id": "TX-1",
            "amount": 12.5,
            "transaction_type": "purchase",
            "description": "Coffee",
            "reference_number": "ref-1",
            "status": "completed",
            "currency": "EUR",
            "currency_symbol": "€",
            "merchant_name": "Cafe",
            "merchant_category": "food",
            "location": "Berlin",
            "is_international": False,
            "channel": "card",
            "direction": "debit",
        }
    )
    return transaction, timestamp


def test_transaction_to_dict_has_stable_keys_values_and_datetime(monkeypatch) -> None:
    transaction, timestamp = _transaction(monkeypatch)

    result = transaction.to_dict()

    assert list(result) == [
        "transaction_id",
        "transaction_date",
        "amount",
        "transaction_type",
        "description",
        "reference_number",
        "status",
        "currency",
        "currency_symbol",
        "merchant_name",
        "merchant_category",
        "location",
        "is_international",
        "channel",
        "direction",
    ]
    assert result == {
        "transaction_id": "TX-1",
        "transaction_date": timestamp,
        "amount": 12.5,
        "transaction_type": "purchase",
        "description": "Coffee",
        "reference_number": "ref-1",
        "status": "completed",
        "currency": "EUR",
        "currency_symbol": "€",
        "merchant_name": "Cafe",
        "merchant_category": "food",
        "location": "Berlin",
        "is_international": False,
        "channel": "card",
        "direction": "debit",
    }
    assert result["transaction_date"] is timestamp


def test_transaction_to_dict_includes_optional_account_and_repeats_cached_values(monkeypatch) -> None:
    account = _account()
    account_data = account.to_dict()
    transaction, _ = _transaction(monkeypatch, account)

    first = transaction.to_dict()
    second = transaction.to_dict()

    assert list(first)[-1] == "account"
    assert first["account"] == account_data
    assert second == first


def test_bank_account_to_dict_has_stable_keys_and_datetime_values() -> None:
    account = _account()

    first = account.to_dict()
    second = account.to_dict()

    assert list(first) == [
        "account_number",
        "iban",
        "account_type",
        "balance",
        "currency",
        "created_date",
        "last_transaction_date",
        "bank_name",
        "bank_code",
        "bic",
        "bin",
    ]
    assert first == second
    assert first["created_date"] is account.created_date
    assert first["last_transaction_date"] is account.last_transaction_date


def test_transaction_to_dict_omits_absent_optional_account(monkeypatch) -> None:
    transaction, _ = _transaction(monkeypatch)

    assert "account" not in transaction.to_dict()


def test_seeded_transaction_serialization_replays() -> None:
    first = Transaction(TransactionGenerator(rng=Random(20260929))).to_dict()
    second = Transaction(TransactionGenerator(rng=Random(20260929))).to_dict()

    assert first == second
