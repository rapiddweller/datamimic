# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import unittest
from unittest.mock import patch

from datamimic_ce.entities.payment_entity import PaymentEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestPaymentEntity(unittest.TestCase):
    """Test cases for the PaymentEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.payment_entity = PaymentEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of PaymentEntity."""
        self.assertEqual(self.payment_entity._locale, "en")
        self.assertEqual(self.payment_entity._min_amount, 0.01)
        self.assertEqual(self.payment_entity._max_amount, 10000.00)
        self.assertIsNone(self.payment_entity._dataset)
        # Check that start_date and end_date are set correctly
        self.assertIsInstance(self.payment_entity._start_date, datetime.datetime)
        self.assertIsInstance(self.payment_entity._end_date, datetime.datetime)
        self.assertLess(self.payment_entity._start_date, self.payment_entity._end_date)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        payment_entity = PaymentEntity(
            self.class_factory_util,
            locale="de",
            min_amount=5.00,
            max_amount=500.00,
            start_date=start_date,
            end_date=end_date,
            dataset="test_dataset"
        )
        self.assertEqual(payment_entity._locale, "de")
        self.assertEqual(payment_entity._min_amount, 5.00)
        self.assertEqual(payment_entity._max_amount, 500.00)
        self.assertEqual(payment_entity._start_date, start_date)
        self.assertEqual(payment_entity._end_date, end_date)
        self.assertEqual(payment_entity._dataset, "test_dataset")

    def test_payment_id_generation(self):
        """Test payment ID generation."""
        payment_id = self.payment_entity.payment_id
        self.assertTrue(payment_id.startswith("PAY-"))
        self.assertEqual(len(payment_id), 16)  # "PAY-" + 12 hex chars

    def test_method_generation(self):
        """Test payment method generation."""
        method = self.payment_entity.method
        self.assertIn(method, PaymentEntity.PAYMENT_METHODS)

    def test_status_generation(self):
        """Test payment status generation."""
        status = self.payment_entity.status
        self.assertIn(status, PaymentEntity.PAYMENT_STATUSES)

    def test_amount_generation(self):
        """Test amount generation."""
        amount = self.payment_entity.amount
        self.assertIsInstance(amount, float)
        self.assertGreaterEqual(amount, self.payment_entity._min_amount)
        self.assertLessEqual(amount, self.payment_entity._max_amount)

    def test_timestamp_generation(self):
        """Test timestamp generation."""
        timestamp = self.payment_entity.timestamp
        self.assertIsInstance(timestamp, datetime.datetime)
        self.assertGreaterEqual(timestamp, self.payment_entity._start_date)
        self.assertLessEqual(timestamp, self.payment_entity._end_date)

    def test_currency_generation(self):
        """Test currency generation."""
        currency = self.payment_entity.currency
        self.assertIn(currency, PaymentEntity.CURRENCY_CODES)

    def test_processor_generation(self):
        """Test payment processor generation."""
        processor = self.payment_entity.processor
        self.assertIn(processor, PaymentEntity.PAYMENT_PROCESSORS)

    def test_invoice_id_generation(self):
        """Test invoice ID generation."""
        invoice_id = self.payment_entity.invoice_id
        self.assertTrue(invoice_id.startswith("INV-"))
        self.assertEqual(len(invoice_id), 12)  # "INV-" + 8 hex chars

    def test_customer_id_generation(self):
        """Test customer ID generation."""
        customer_id = self.payment_entity.customer_id
        self.assertTrue(customer_id.startswith("CUST-"))
        self.assertEqual(len(customer_id), 13)  # "CUST-" + 8 hex chars

    def test_description_generation(self):
        """Test description generation."""
        # Mock the method to ensure consistent test results
        with patch.object(PaymentEntity, 'method', return_value="CREDIT_CARD"):
            description = self.payment_entity.description
            self.assertIsInstance(description, str)
            self.assertGreater(len(description), 0)

    def test_fee_generation(self):
        """Test fee generation."""
        # We can't easily mock the property, so we'll just verify the fee is a float
        fee = self.payment_entity.fee
        self.assertIsInstance(fee, float)
        # The fee should be positive
        self.assertGreater(fee, 0.0)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        payment_dict = self.payment_entity.to_dict()
        self.assertIsInstance(payment_dict, dict)
        expected_keys = [
            "payment_id", "method", "status", "amount", "timestamp",
            "currency", "processor", "invoice_id", "customer_id",
            "description", "fee"
        ]
        for key in expected_keys:
            self.assertIn(key, payment_dict)

    def test_generate_batch(self):
        """Test batch generation."""
        batch_size = 5
        payments = self.payment_entity.generate_batch(count=batch_size)
        self.assertEqual(len(payments), batch_size)
        for payment in payments:
            self.assertIsInstance(payment, dict)
            self.assertIn("payment_id", payment)
            self.assertIn("method", payment)
            self.assertIn("status", payment)
            self.assertIn("amount", payment)
            self.assertIn("timestamp", payment)

    def test_reset(self):
        """Test reset functionality."""
        # Get initial values
        initial_payment_id = self.payment_entity.payment_id
        initial_invoice_id = self.payment_entity.invoice_id
        
        # Reset the entity
        self.payment_entity.reset()
        
        # Get new values
        new_payment_id = self.payment_entity.payment_id
        new_invoice_id = self.payment_entity.invoice_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_payment_id, new_payment_id)
        self.assertNotEqual(initial_invoice_id, new_invoice_id)


if __name__ == "__main__":
    unittest.main() 