import datetime

import pytest

from datamimic_ce.domains.finance.models.transaction import Transaction
from datamimic_ce.domains.finance.services.transaction_service import TransactionService


class TestTransaction:
    _supported_datasets = ["US", "DE"]

    def _test_single_transaction(self, transaction: Transaction):
        assert isinstance(transaction, Transaction)
        assert isinstance(transaction.transaction_id, str)
        assert isinstance(transaction.transaction_date, datetime.datetime)
        assert isinstance(transaction.amount, float)
        assert isinstance(transaction.transaction_type, str)
        assert isinstance(transaction.description, str)
        assert isinstance(transaction.reference_number, str)
        assert isinstance(transaction.status, str)
        assert isinstance(transaction.currency, str)
        assert isinstance(transaction.currency_symbol, str)
        assert isinstance(transaction.merchant_name, str)
        assert isinstance(transaction.merchant_category, str)
        assert isinstance(transaction.location, str)
        assert isinstance(transaction.is_international, bool)
        assert isinstance(transaction.channel, str)
        assert isinstance(transaction.direction, str)

        assert transaction.transaction_id is not None
        assert transaction.transaction_id != ""
        assert transaction.transaction_date is not None
        assert transaction.amount is not None
        assert transaction.amount > 0
        assert transaction.transaction_type is not None
        assert transaction.transaction_type != ""
        assert transaction.description is not None
        assert transaction.description != ""
        assert transaction.reference_number is not None
        assert transaction.reference_number != ""
        assert transaction.status is not None
        assert transaction.status != ""
        assert transaction.currency is not None
        assert transaction.currency != ""
        assert transaction.currency_symbol is not None
        assert transaction.currency_symbol != ""
        assert transaction.merchant_name is not None
        assert transaction.merchant_name != ""
        assert transaction.merchant_category is not None
        assert transaction.merchant_category != ""
        assert transaction.location is not None
        assert transaction.location != ""
        assert transaction.is_international is not None
        assert transaction.channel is not None
        assert transaction.channel != ""
        assert transaction.direction in ["credit", "debit"]

    def test_generate_single_transaction(self):
        transaction_service = TransactionService()
        transaction = transaction_service.generate()
        self._test_single_transaction(transaction)

    def test_generate_multiple_transactions(self):
        transaction_service = TransactionService()
        transactions = transaction_service.generate_batch(10)
        assert len(transactions) == 10
        for transaction in transactions:
            self._test_single_transaction(transaction)

    def test_transaction_property_cache(self):
        transaction_service = TransactionService()
        transaction = transaction_service.generate()
        assert transaction is not None
        assert transaction.transaction_id == transaction.transaction_id
        assert transaction.transaction_date == transaction.transaction_date
        assert transaction.amount == transaction.amount
        assert transaction.transaction_type == transaction.transaction_type
        assert transaction.description == transaction.description
        assert transaction.reference_number == transaction.reference_number
        assert transaction.status == transaction.status
        assert transaction.currency == transaction.currency
        assert transaction.currency_symbol == transaction.currency_symbol
        assert transaction.merchant_name == transaction.merchant_name
        assert transaction.merchant_category == transaction.merchant_category
        assert transaction.location == transaction.location
        assert transaction.is_international == transaction.is_international
        assert transaction.channel == transaction.channel
        assert transaction.direction == transaction.direction

    @pytest.mark.flaky(reruns=3)
    def test_two_different_entities(self):
        transaction_service = TransactionService()
        transaction1 = transaction_service.generate()
        transaction2 = transaction_service.generate()
        assert transaction1 is not None
        assert transaction2 is not None
        assert transaction1.transaction_id != transaction2.transaction_id
        assert transaction1.reference_number != transaction2.reference_number

        # The following comparisons might occasionally be the same by coincidence,
        # but generally they should be different in most cases
        assert any(
            [
                transaction1.transaction_date != transaction2.transaction_date,
                transaction1.amount != transaction2.amount,
                transaction1.transaction_type != transaction2.transaction_type,
                transaction1.description != transaction2.description,
                transaction1.status != transaction2.status,
                transaction1.merchant_name != transaction2.merchant_name,
                transaction1.merchant_category != transaction2.merchant_category,
                transaction1.location != transaction2.location,
                transaction1.channel != transaction2.channel,
                transaction1.direction != transaction2.direction,
            ]
        )

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        transaction_service = TransactionService(dataset=dataset)
        transaction = transaction_service.generate()
        self._test_single_transaction(transaction)

        # Test currency codes and symbols for specific datasets
        if dataset == "US":
            assert transaction.currency in ["USD", "CAD", "MXN", "EUR", "GBP", "JPY", "AUD", "CHF"]
            if transaction.currency == "USD":
                assert transaction.currency_symbol == "$"
            elif transaction.currency == "EUR":
                assert transaction.currency_symbol == "€"
            elif transaction.currency == "GBP":
                assert transaction.currency_symbol == "£"
        elif dataset == "DE":
            assert transaction.currency in ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "JPY", "SGD", "AUD"]
            if transaction.currency == "EUR":
                assert transaction.currency_symbol == "€"
            elif transaction.currency == "USD":
                assert transaction.currency_symbol == "$"
            elif transaction.currency == "GBP":
                assert transaction.currency_symbol == "£"

    def test_to_dict_method(self):
        transaction_service = TransactionService()
        transaction = transaction_service.generate()
        transaction_dict = transaction.to_dict()

        assert isinstance(transaction_dict, dict)
        assert "transaction_id" in transaction_dict
        assert "transaction_date" in transaction_dict
        assert "amount" in transaction_dict
        assert "transaction_type" in transaction_dict
        assert "description" in transaction_dict
        assert "reference_number" in transaction_dict
        assert "status" in transaction_dict
        assert "currency" in transaction_dict
        assert "currency_symbol" in transaction_dict
        assert "merchant_name" in transaction_dict
        assert "merchant_category" in transaction_dict
        assert "location" in transaction_dict
        assert "is_international" in transaction_dict
        assert "channel" in transaction_dict
        assert "direction" in transaction_dict
