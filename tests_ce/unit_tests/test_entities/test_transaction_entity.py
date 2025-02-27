# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import re
import unittest
from datetime import datetime

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
        self.assertIsNone(self.transaction_entity._dataset)
        
        # Test with custom parameters
        transaction_entity = TransactionEntity(
            self.class_factory_util,
            locale="fr",
            dataset="test_dataset",
            min_amount=100,
            max_amount=5000
        )
        self.assertEqual(transaction_entity._locale, "fr")
        self.assertEqual(transaction_entity._dataset, "test_dataset")
        self.assertEqual(transaction_entity._min_amount, 100)
        self.assertEqual(transaction_entity._max_amount, 5000)

    def test_transaction_id_generation(self):
        """Test transaction_id generation."""
        transaction_id = self.transaction_entity.transaction_id
        
        # Check format (e.g., "TXN-12345-ABCDE")
        self.assertTrue(re.match(r"TXN-\d+-[A-Z0-9]+", transaction_id))
        
        # Check that it's consistent
        self.assertEqual(transaction_id, self.transaction_entity.transaction_id)
        
        # Check that it changes after reset
        self.transaction_entity.reset()
        self.assertNotEqual(transaction_id, self.transaction_entity.transaction_id)

    def test_date_generation(self):
        """Test date generation."""
        date = self.transaction_entity.date
        
        # Check that it's a string
        self.assertIsInstance(date, str)
        
        # Check that it's a valid date format (YYYY-MM-DD)
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            self.fail("date is not in the expected format YYYY-MM-DD")

    def test_time_generation(self):
        """Test time generation."""
        time = self.transaction_entity.time
        
        # Check that it's a string
        self.assertIsInstance(time, str)
        
        # Check that it's a valid time format (HH:MM:SS)
        try:
            datetime.strptime(time, "%H:%M:%S")
        except ValueError:
            self.fail("time is not in the expected format HH:MM:SS")

    def test_type_generation(self):
        """Test type generation."""
        transaction_type = self.transaction_entity.type
        
        # Check that it's a string
        self.assertIsInstance(transaction_type, str)
        
        # Check that it's one of the expected types
        self.assertIn(transaction_type, TransactionEntity.TRANSACTION_TYPES)
        
        # Test with custom type
        transaction_entity = TransactionEntity(self.class_factory_util, transaction_type="CUSTOM")
        self.assertEqual(transaction_entity.type, "CUSTOM")

    def test_amount_generation(self):
        """Test amount generation."""
        amount = self.transaction_entity.amount
        
        # Check that it's a float
        self.assertIsInstance(amount, float)
        
        # Check that it's within default range
        self.assertTrue(0.01 <= amount <= 10000.00)
        
        # Test with custom amount range
        transaction_entity = TransactionEntity(self.class_factory_util, min_amount=100, max_amount=500)
        self.assertTrue(100 <= transaction_entity.amount <= 500)

    def test_currency_generation(self):
        """Test currency generation."""
        currency = self.transaction_entity.currency
        
        # Check that it's a string
        self.assertIsInstance(currency, str)
        
        # Check that it's one of the expected currencies
        self.assertIn(currency, TransactionEntity.CURRENCIES)
        
        # Test with custom currency
        transaction_entity = TransactionEntity(self.class_factory_util, currency="BTC")
        self.assertEqual(transaction_entity.currency, "BTC")

    def test_status_generation(self):
        """Test status generation."""
        status = self.transaction_entity.status
        
        # Check that it's a string
        self.assertIsInstance(status, str)
        
        # Check that it's one of the expected statuses
        self.assertIn(status, TransactionEntity.STATUSES)
        
        # Test with custom status
        transaction_entity = TransactionEntity(self.class_factory_util, status="CUSTOM")
        self.assertEqual(transaction_entity.status, "CUSTOM")

    def test_source_generation(self):
        """Test source generation."""
        source = self.transaction_entity.source
        
        # Check that it's a string
        self.assertIsInstance(source, str)
        
        # Check that it's not empty
        self.assertTrue(len(source) > 0)

    def test_destination_generation(self):
        """Test destination generation."""
        destination = self.transaction_entity.destination
        
        # Check that it's a string
        self.assertIsInstance(destination, str)
        
        # Check that it's not empty
        self.assertTrue(len(destination) > 0)

    def test_description_generation(self):
        """Test description generation."""
        description = self.transaction_entity.description
        
        # Check that it's a string
        self.assertIsInstance(description, str)
        
        # Check that it's not empty
        self.assertTrue(len(description) > 0)

    def test_metadata_generation(self):
        """Test metadata generation."""
        metadata = self.transaction_entity.metadata
        
        # Check that it's a dictionary
        self.assertIsInstance(metadata, dict)
        
        # Check that it has the expected keys
        self.assertIn("ip_address", metadata)
        self.assertIn("device", metadata)
        self.assertIn("location", metadata)
        self.assertIn("user_agent", metadata)

    def test_to_dict(self):
        """Test to_dict method."""
        transaction_dict = self.transaction_entity.to_dict()
        
        # Check that it's a dictionary
        self.assertIsInstance(transaction_dict, dict)
        
        # Check that it has all the expected keys
        expected_keys = [
            "transaction_id", "date", "time", "type", "amount", "currency",
            "status", "source", "destination", "description", "metadata"
        ]
        for key in expected_keys:
            self.assertIn(key, transaction_dict)
        
        # Check that the values match the properties
        self.assertEqual(transaction_dict["transaction_id"], self.transaction_entity.transaction_id)
        self.assertEqual(transaction_dict["amount"], self.transaction_entity.amount)
        self.assertEqual(transaction_dict["status"], self.transaction_entity.status)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        transactions = self.transaction_entity.generate_batch(count=batch_size)
        
        # Check that it returns a list of the correct size
        self.assertIsInstance(transactions, list)
        self.assertEqual(len(transactions), batch_size)
        
        # Check that each item is a dictionary with the expected keys
        for transaction in transactions:
            self.assertIsInstance(transaction, dict)
            self.assertIn("transaction_id", transaction)
            self.assertIn("amount", transaction)
            self.assertIn("type", transaction)
            
        # Check that the transactions are unique
        transaction_ids = [transaction["transaction_id"] for transaction in transactions]
        self.assertEqual(len(transaction_ids), len(set(transaction_ids)))

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_transaction_id = self.transaction_entity.transaction_id
        initial_amount = self.transaction_entity.amount
        
        # Reset the entity
        self.transaction_entity.reset()
        
        # Check that values have changed
        self.assertNotEqual(initial_transaction_id, self.transaction_entity.transaction_id)
        self.assertNotEqual(initial_amount, self.transaction_entity.amount)

    def test_class_factory_integration(self):
        """Test integration with ClassFactoryCEUtil."""
        # Test the factory method directly
        transaction = ClassFactoryCEUtil.get_transaction_entity(
            locale="en_US", 
            min_amount=50, 
            max_amount=1000
        )
        
        # Check that it returns a TransactionEntity instance
        self.assertIsInstance(transaction, TransactionEntity)
        
        # Check that the parameters were passed correctly
        self.assertEqual(transaction._locale, "en_US")
        self.assertEqual(transaction._min_amount, 50)
        self.assertEqual(transaction._max_amount, 1000)


if __name__ == '__main__':
    unittest.main() 