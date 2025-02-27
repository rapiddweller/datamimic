# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import unittest
from unittest.mock import patch

from datamimic_ce.entities.transaction_entity import TransactionEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestTransactionEntity(unittest.TestCase):
    """Test cases for the TransactionEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.transaction_entity = TransactionEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of TransactionEntity."""
        self.assertEqual(self.transaction_entity._locale, "en")
        self.assertEqual(self.transaction_entity._min_amount, 0.01)
        self.assertEqual(self.transaction_entity._max_amount, 10000.00)
        self.assertIsNone(self.transaction_entity._dataset)
        # Check that start_date and end_date are set correctly
        self.assertIsInstance(self.transaction_entity._start_date, datetime.datetime)
        self.assertIsInstance(self.transaction_entity._end_date, datetime.datetime)
        self.assertLess(self.transaction_entity._start_date, self.transaction_entity._end_date)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        transaction_entity = TransactionEntity(
            self.class_factory_util,
            locale="de",
            min_amount=5.00,
            max_amount=500.00,
            start_date=start_date,
            end_date=end_date,
            dataset="test_dataset"
        )
        self.assertEqual(transaction_entity._locale, "de")
        self.assertEqual(transaction_entity._min_amount, 5.00)
        self.assertEqual(transaction_entity._max_amount, 500.00)
        self.assertEqual(transaction_entity._start_date, start_date)
        self.assertEqual(transaction_entity._end_date, end_date)
        self.assertEqual(transaction_entity._dataset, "test_dataset")

    def test_transaction_id_generation(self):
        """Test transaction ID generation."""
        transaction_id = self.transaction_entity.transaction_id
        self.assertTrue(transaction_id.startswith("TXN-"))
        self.assertEqual(len(transaction_id), 16)  # "TXN-" + 12 hex chars

    def test_amount_generation(self):
        """Test amount generation."""
        amount = self.transaction_entity.amount
        self.assertIsInstance(amount, float)
        self.assertGreaterEqual(amount, self.transaction_entity._min_amount)
        self.assertLessEqual(amount, self.transaction_entity._max_amount)

    def test_timestamp_generation(self):
        """Test timestamp generation."""
        timestamp = self.transaction_entity.timestamp
        self.assertIsInstance(timestamp, datetime.datetime)
        self.assertGreaterEqual(timestamp, self.transaction_entity._start_date)
        self.assertLessEqual(timestamp, self.transaction_entity._end_date)

    def test_type_generation(self):
        """Test transaction type generation."""
        transaction_type = self.transaction_entity.type
        self.assertIn(transaction_type, TransactionEntity.TRANSACTION_TYPES)

    def test_status_generation(self):
        """Test transaction status generation."""
        status = self.transaction_entity.status
        self.assertIn(status, TransactionEntity.TRANSACTION_STATUSES)

    def test_currency_generation(self):
        """Test currency generation."""
        currency = self.transaction_entity.currency
        self.assertIn(currency, TransactionEntity.CURRENCY_CODES)

    def test_description_generation(self):
        """Test description generation."""
        # Mock the type to ensure consistent test results
        with patch.object(TransactionEntity, 'type', return_value="PURCHASE"):
            description = self.transaction_entity.description
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 0)

    def test_reference_id_generation(self):
        """Test reference ID generation."""
        reference_id = self.transaction_entity.reference_id
        self.assertTrue(reference_id.startswith("REF-"))
        self.assertEqual(len(reference_id), 12)  # "REF-" + 8 hex chars

    def test_fee_generation(self):
        """Test fee generation."""
        # We can't easily mock the property, so we'll just verify the fee is a float
        fee = self.transaction_entity.fee
        self.assertIsInstance(fee, float)
        # The fee should be positive
        self.assertGreater(fee, 0.0)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        transaction_dict = self.transaction_entity.to_dict()
        self.assertIsInstance(transaction_dict, dict)
        expected_keys = [
            "transaction_id", "amount", "timestamp", "type", "status",
            "currency", "description", "reference_id", "fee"
        ]
        for key in expected_keys:
            self.assertIn(key, transaction_dict)

    def test_generate_batch(self):
        """Test batch generation."""
        batch_size = 5
        transactions = self.transaction_entity.generate_batch(count=batch_size)
        self.assertEqual(len(transactions), batch_size)
        for transaction in transactions:
            self.assertIsInstance(transaction, dict)
            self.assertIn("transaction_id", transaction)
            self.assertIn("amount", transaction)
            self.assertIn("timestamp", transaction)
            self.assertIn("type", transaction)
            self.assertIn("status", transaction)

    def test_reset(self):
        """Test reset functionality."""
        # Get initial values
        initial_transaction_id = self.transaction_entity.transaction_id
        initial_reference_id = self.transaction_entity.reference_id
        
        # Reset the entity
        self.transaction_entity.reset()
        
        # Get new values
        new_transaction_id = self.transaction_entity.transaction_id
        new_reference_id = self.transaction_entity.reference_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_transaction_id, new_transaction_id)
        self.assertNotEqual(initial_reference_id, new_reference_id)


if __name__ == "__main__":
    unittest.main() 