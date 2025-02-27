# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest

from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestTransactionEntityFactory(unittest.TestCase):
    """Integration tests for the TransactionEntity factory."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()

    def test_get_transaction_entity_default(self):
        """Test getting a TransactionEntity with default parameters."""
        transaction_entity = self.class_factory_util.get_transaction_entity()
        
        # Verify the entity type and basic properties
        self.assertEqual(transaction_entity._locale, "en")
        self.assertEqual(transaction_entity._min_amount, 0.01)
        self.assertEqual(transaction_entity._max_amount, 10000.00)
        self.assertIsNone(transaction_entity._dataset)
        
        # Verify that the entity can generate data
        transaction = transaction_entity.to_dict()
        self.assertIsInstance(transaction, dict)
        self.assertIn("transaction_id", transaction)
        self.assertIn("amount", transaction)
        self.assertIn("date", transaction)
        self.assertIn("time", transaction)
        self.assertIn("type", transaction)
        self.assertIn("status", transaction)
        self.assertIn("currency", transaction)
        self.assertIn("description", transaction)
        self.assertIn("source", transaction)
        self.assertIn("destination", transaction)
        self.assertIn("metadata", transaction)

        # Verify the amount is within the expected range
        self.assertGreaterEqual(transaction["amount"], transaction_entity._min_amount)
        self.assertLessEqual(transaction["amount"], transaction_entity._max_amount)

    def test_get_transaction_entity_with_params(self):
        """Test getting a TransactionEntity with custom parameters."""
        transaction_entity = self.class_factory_util.get_transaction_entity(
            locale="de",
            min_amount=5.00,
            max_amount=500.00,
            transaction_type="PAYMENT",
            currency="EUR",
            status="COMPLETED",
            dataset="test_dataset"
        )
        
        # Verify the custom parameters were applied
        self.assertEqual(transaction_entity._locale, "de")
        self.assertEqual(transaction_entity._min_amount, 5.00)
        self.assertEqual(transaction_entity._max_amount, 500.00)
        self.assertEqual(transaction_entity._transaction_type, "PAYMENT")
        self.assertEqual(transaction_entity._currency, "EUR")
        self.assertEqual(transaction_entity._status, "COMPLETED")
        self.assertEqual(transaction_entity._dataset, "test_dataset")
        
        # Verify the entity generates data with custom parameters
        transaction = transaction_entity.to_dict()
        self.assertIsInstance(transaction, dict)
        self.assertGreaterEqual(transaction["amount"], 5.00)
        self.assertLessEqual(transaction["amount"], 500.00)
        self.assertEqual(transaction["type"], "PAYMENT")
        self.assertEqual(transaction["currency"], "EUR")
        self.assertEqual(transaction["status"], "COMPLETED")

    def test_get_transaction_entity_batch_generation(self):
        """Test batch generation using factory-created TransactionEntity."""
        transaction_entity = self.class_factory_util.get_transaction_entity()
        
        # Generate a batch of transactions
        batch_size = 10
        transactions = transaction_entity.generate_batch(count=batch_size)
        
        # Verify the batch size and transaction structure
        self.assertEqual(len(transactions), batch_size)
        for transaction in transactions:
            self.assertIsInstance(transaction, dict)
            self.assertIn("transaction_id", transaction)
            self.assertIn("amount", transaction)
            self.assertIn("date", transaction)
            self.assertIn("time", transaction)
            self.assertIn("type", transaction)
            self.assertIn("status", transaction)
            self.assertIn("currency", transaction)
            self.assertIn("description", transaction)
            self.assertIn("source", transaction)
            self.assertIn("destination", transaction)
            self.assertIn("metadata", transaction)

    def test_transaction_entity_reset(self):
        """Test resetting a factory-created TransactionEntity."""
        transaction_entity = self.class_factory_util.get_transaction_entity()
        
        # Get initial values
        initial_transaction_id = transaction_entity.transaction_id
        initial_amount = transaction_entity.amount
        
        # Reset the entity
        transaction_entity.reset()
        
        # Get new values
        new_transaction_id = transaction_entity.transaction_id
        new_amount = transaction_entity.amount
        
        # Values should be different after reset
        self.assertNotEqual(initial_transaction_id, new_transaction_id)
        self.assertNotEqual(initial_amount, new_amount)

    def test_transaction_type_validation(self):
        """Test that transaction types are valid."""
        transaction_entity = self.class_factory_util.get_transaction_entity()
        
        # Check that the transaction type is in the predefined list
        transaction = transaction_entity.to_dict()
        self.assertIn(transaction["type"], transaction_entity.TRANSACTION_TYPES)

    def test_transaction_status_validation(self):
        """Test that transaction statuses are valid."""
        transaction_entity = self.class_factory_util.get_transaction_entity()
        
        # Check that the transaction status is in the predefined list
        transaction = transaction_entity.to_dict()
        self.assertIn(transaction["status"], transaction_entity.STATUSES)


if __name__ == "__main__":
    unittest.main() 