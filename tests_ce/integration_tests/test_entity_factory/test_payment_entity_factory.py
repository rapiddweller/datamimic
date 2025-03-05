# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import unittest

from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestPaymentEntityFactory(unittest.TestCase):
    """Integration tests for the PaymentEntity factory."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()

    def test_get_payment_entity_default(self):
        """Test getting a PaymentEntity with default parameters."""
        payment_entity = self.class_factory_util.get_payment_entity()
        
        # Verify the entity type and basic properties
        self.assertEqual(payment_entity._locale, "en")
        self.assertEqual(payment_entity._min_amount, 0.01)
        self.assertEqual(payment_entity._max_amount, 10000.00)
        self.assertIsNone(payment_entity._dataset)
        
        # Verify that the entity can generate data
        payment = payment_entity.to_dict()
        self.assertIsInstance(payment, dict)
        self.assertIn("payment_id", payment)
        self.assertIn("method", payment)
        self.assertIn("status", payment)
        self.assertIn("amount", payment)
        self.assertIn("timestamp", payment)
        self.assertIn("currency", payment)
        self.assertIn("processor", payment)

        # Verify the amount is within the expected range
        self.assertGreaterEqual(payment["amount"], payment_entity._min_amount)
        self.assertLessEqual(payment["amount"], payment_entity._max_amount)

    def test_get_payment_entity_with_params(self):
        """Test getting a PaymentEntity with custom parameters."""
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        payment_entity = self.class_factory_util.get_payment_entity(
            locale="de",
            min_amount=5.00,
            max_amount=500.00,
            start_date=start_date,
            end_date=end_date,
            dataset="test_dataset"
        )
        
        # Verify the custom parameters were applied
        self.assertEqual(payment_entity._locale, "de")
        self.assertEqual(payment_entity._min_amount, 5.00)
        self.assertEqual(payment_entity._max_amount, 500.00)
        self.assertEqual(payment_entity._start_date, start_date)
        self.assertEqual(payment_entity._end_date, end_date)
        self.assertEqual(payment_entity._dataset, "test_dataset")
        
        # Verify the entity generates data with custom parameters
        payment = payment_entity.to_dict()
        self.assertIsInstance(payment, dict)
        self.assertGreaterEqual(payment["amount"], 5.00)
        self.assertLessEqual(payment["amount"], 500.00)
        # Verify payment timestamp is within the specified range
        self.assertGreaterEqual(payment["timestamp"], start_date)
        self.assertLessEqual(payment["timestamp"], end_date)

    def test_get_payment_entity_batch_generation(self):
        """Test batch generation using factory-created PaymentEntity."""
        payment_entity = self.class_factory_util.get_payment_entity()
        
        # Generate a batch of payments
        batch_size = 10
        payments = payment_entity.generate_batch(count=batch_size)
        
        # Verify the batch size and payment structure
        self.assertEqual(len(payments), batch_size)
        for payment in payments:
            self.assertIsInstance(payment, dict)
            self.assertIn("payment_id", payment)
            self.assertIn("method", payment)
            self.assertIn("status", payment)
            self.assertIn("amount", payment)
            self.assertIn("timestamp", payment)
            self.assertIn("currency", payment)
            self.assertIn("processor", payment)

    def test_payment_entity_reset(self):
        """Test resetting a factory-created PaymentEntity."""
        payment_entity = self.class_factory_util.get_payment_entity()
        
        # Get initial values
        initial_payment_id = payment_entity.payment_id
        initial_invoice_id = payment_entity.invoice_id
        
        # Reset the entity
        payment_entity.reset()
        
        # Get new values
        new_payment_id = payment_entity.payment_id
        new_invoice_id = payment_entity.invoice_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_payment_id, new_payment_id)
        self.assertNotEqual(initial_invoice_id, new_invoice_id)

    def test_payment_method_validation(self):
        """Test that payment methods are valid."""
        payment_entity = self.class_factory_util.get_payment_entity()
        
        # Check that the payment method is in the predefined list
        payment = payment_entity.to_dict()
        self.assertIn(payment["method"], payment_entity.PAYMENT_METHODS)


if __name__ == "__main__":
    unittest.main() 