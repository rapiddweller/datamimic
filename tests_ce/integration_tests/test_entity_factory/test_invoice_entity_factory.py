# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import unittest

from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestInvoiceEntityFactory(unittest.TestCase):
    """Integration tests for the InvoiceEntity factory."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()

    def test_get_invoice_entity_default(self):
        """Test getting an InvoiceEntity with default parameters."""
        invoice_entity = self.class_factory_util.get_invoice_entity()
        
        # Verify the entity type and basic properties
        self.assertEqual(invoice_entity._locale, "en")
        self.assertEqual(invoice_entity._min_amount, 10.00)
        self.assertEqual(invoice_entity._max_amount, 10000.00)
        self.assertIsNone(invoice_entity._dataset)
        
        # Verify that the entity can generate data
        invoice = invoice_entity.to_dict()
        self.assertIsInstance(invoice, dict)
        self.assertIn("invoice_id", invoice)
        self.assertIn("order_id", invoice)
        self.assertIn("customer_id", invoice)
        self.assertIn("date", invoice)
        self.assertIn("due_date", invoice)
        self.assertIn("amount", invoice)
        self.assertIn("status", invoice)
        self.assertIn("payment_terms", invoice)

        # Verify the amount is within the expected range
        self.assertGreaterEqual(invoice["amount"], invoice_entity._min_amount)
        self.assertLessEqual(invoice["amount"], invoice_entity._max_amount)

    def test_get_invoice_entity_with_params(self):
        """Test getting an InvoiceEntity with custom parameters."""
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        invoice_entity = self.class_factory_util.get_invoice_entity(
            locale="de",
            min_amount=50.00,
            max_amount=5000.00,
            start_date=start_date,
            end_date=end_date,
            dataset="test_dataset"
        )
        
        # Verify the custom parameters were applied
        self.assertEqual(invoice_entity._locale, "de")
        self.assertEqual(invoice_entity._min_amount, 50.00)
        self.assertEqual(invoice_entity._max_amount, 5000.00)
        self.assertEqual(invoice_entity._start_date, start_date)
        self.assertEqual(invoice_entity._end_date, end_date)
        self.assertEqual(invoice_entity._dataset, "test_dataset")
        
        # Verify the entity generates data with custom parameters
        invoice = invoice_entity.to_dict()
        self.assertIsInstance(invoice, dict)
        self.assertGreaterEqual(invoice["amount"], 50.00)
        self.assertLessEqual(invoice["amount"], 5000.00)
        # Verify invoice date is within the specified range
        self.assertGreaterEqual(invoice["date"], start_date)
        self.assertLessEqual(invoice["date"], end_date)

    def test_get_invoice_entity_batch_generation(self):
        """Test batch generation using factory-created InvoiceEntity."""
        invoice_entity = self.class_factory_util.get_invoice_entity()
        
        # Generate a batch of invoices
        batch_size = 10
        invoices = invoice_entity.generate_batch(count=batch_size)
        
        # Verify the batch size and invoice structure
        self.assertEqual(len(invoices), batch_size)
        for invoice in invoices:
            self.assertIsInstance(invoice, dict)
            self.assertIn("invoice_id", invoice)
            self.assertIn("order_id", invoice)
            self.assertIn("customer_id", invoice)
            self.assertIn("date", invoice)
            self.assertIn("due_date", invoice)
            self.assertIn("amount", invoice)
            self.assertIn("status", invoice)

    def test_invoice_entity_reset(self):
        """Test resetting a factory-created InvoiceEntity."""
        invoice_entity = self.class_factory_util.get_invoice_entity()
        
        # Get initial values
        initial_invoice_id = invoice_entity.invoice_id
        initial_order_id = invoice_entity.order_id
        
        # Reset the entity
        invoice_entity.reset()
        
        # Get new values
        new_invoice_id = invoice_entity.invoice_id
        new_order_id = invoice_entity.order_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_invoice_id, new_invoice_id)
        self.assertNotEqual(initial_order_id, new_order_id)

    def test_due_date_generation(self):
        """Test due date generation based on invoice date and payment terms."""
        invoice_entity = self.class_factory_util.get_invoice_entity()
        
        # Get an invoice and check that due_date is after date
        invoice = invoice_entity.to_dict()
        self.assertGreaterEqual(invoice["due_date"], invoice["date"])


if __name__ == "__main__":
    unittest.main() 