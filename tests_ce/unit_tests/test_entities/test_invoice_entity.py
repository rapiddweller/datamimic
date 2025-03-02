# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import unittest

from datamimic_ce.entities.invoice_entity import InvoiceEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestInvoiceEntity(unittest.TestCase):
    """Test cases for the InvoiceEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.invoice_entity = InvoiceEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of InvoiceEntity."""
        self.assertEqual(self.invoice_entity._locale, "en")
        self.assertEqual(self.invoice_entity._min_amount, 10.00)
        self.assertEqual(self.invoice_entity._max_amount, 10000.00)
        self.assertIsNone(self.invoice_entity._dataset)
        # Check that start_date and end_date are set correctly
        self.assertIsInstance(self.invoice_entity._start_date, datetime.datetime)
        self.assertIsInstance(self.invoice_entity._end_date, datetime.datetime)
        self.assertLess(self.invoice_entity._start_date, self.invoice_entity._end_date)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        invoice_entity = InvoiceEntity(
            self.class_factory_util,
            locale="de",
            min_amount=50.00,
            max_amount=5000.00,
            start_date=start_date,
            end_date=end_date,
            dataset="test_dataset"
        )
        self.assertEqual(invoice_entity._locale, "de")
        self.assertEqual(invoice_entity._min_amount, 50.00)
        self.assertEqual(invoice_entity._max_amount, 5000.00)
        self.assertEqual(invoice_entity._start_date, start_date)
        self.assertEqual(invoice_entity._end_date, end_date)
        self.assertEqual(invoice_entity._dataset, "test_dataset")

    def test_invoice_id_generation(self):
        """Test invoice ID generation."""
        invoice_id = self.invoice_entity.invoice_id
        self.assertTrue(invoice_id.startswith("INV-"))
        self.assertEqual(len(invoice_id), 12)  # "INV-" + 8 hex chars

    def test_order_id_generation(self):
        """Test order ID generation."""
        order_id = self.invoice_entity.order_id
        self.assertTrue(order_id.startswith("ORD-"))
        self.assertEqual(len(order_id), 12)  # "ORD-" + 8 hex chars

    def test_customer_id_generation(self):
        """Test customer ID generation."""
        customer_id = self.invoice_entity.customer_id
        self.assertTrue(customer_id.startswith("CUST-"))
        self.assertEqual(len(customer_id), 13)  # "CUST-" + 8 hex chars

    def test_date_generation(self):
        """Test date generation."""
        date = self.invoice_entity.date
        self.assertIsInstance(date, datetime.datetime)
        self.assertGreaterEqual(date, self.invoice_entity._start_date)
        self.assertLessEqual(date, self.invoice_entity._end_date)

    def test_due_date_generation(self):
        """Test due date generation."""
        # Simply check that due_date is a datetime and is after the invoice date
        due_date = self.invoice_entity.due_date
        self.assertIsInstance(due_date, datetime.datetime)
        self.assertGreaterEqual(due_date, self.invoice_entity.date)

    def test_amount_generation(self):
        """Test amount generation."""
        amount = self.invoice_entity.amount
        self.assertIsInstance(amount, float)
        self.assertGreaterEqual(amount, self.invoice_entity._min_amount)
        self.assertLessEqual(amount, self.invoice_entity._max_amount)

    def test_status_generation(self):
        """Test invoice status generation."""
        status = self.invoice_entity.status
        self.assertIn(status, InvoiceEntity.INVOICE_STATUSES)

    def test_payment_terms_generation(self):
        """Test payment terms generation."""
        payment_terms = self.invoice_entity.payment_terms
        self.assertIn(payment_terms, InvoiceEntity.PAYMENT_TERMS)

    def test_currency_generation(self):
        """Test currency generation."""
        currency = self.invoice_entity.currency
        self.assertIn(currency, InvoiceEntity.CURRENCY_CODES)

    def test_tax_amount_generation(self):
        """Test tax amount generation."""
        tax_amount = self.invoice_entity.tax_amount
        self.assertIsInstance(tax_amount, float)
        # Tax amount should be non-negative
        self.assertGreaterEqual(tax_amount, 0.0)

    def test_discount_amount_generation(self):
        """Test discount amount generation."""
        discount_amount = self.invoice_entity.discount_amount
        self.assertIsInstance(discount_amount, float)
        # Discount amount should be non-negative
        self.assertGreaterEqual(discount_amount, 0.0)

    def test_shipping_amount_generation(self):
        """Test shipping amount generation."""
        shipping_amount = self.invoice_entity.shipping_amount
        self.assertIsInstance(shipping_amount, float)
        # Shipping amount should be non-negative
        self.assertGreaterEqual(shipping_amount, 0.0)

    def test_subtotal_generation(self):
        """Test subtotal generation."""
        subtotal = self.invoice_entity.subtotal
        self.assertIsInstance(subtotal, float)
        # Subtotal should be positive
        self.assertGreater(subtotal, 0.0)

    def test_total_generation(self):
        """Test total generation."""
        total = self.invoice_entity.total
        self.assertIsInstance(total, float)
        # Total should be positive
        self.assertGreater(total, 0.0)

    def test_notes_generation(self):
        """Test notes generation."""
        notes = self.invoice_entity.notes
        # Notes can be None or a string
        if notes is not None:
            self.assertIsInstance(notes, str)

    def test_payment_method_generation(self):
        """Test payment method generation."""
        payment_method = self.invoice_entity.payment_method
        # Payment method can be None or a string
        if payment_method is not None:
            # Just check that it's a string
            self.assertIsInstance(payment_method, str)

    def test_billing_address_generation(self):
        """Test billing address generation."""
        billing_address = self.invoice_entity.billing_address
        self.assertIsInstance(billing_address, dict)
        expected_keys = ["street", "city", "state", "postal_code", "country"]
        for key in expected_keys:
            self.assertIn(key, billing_address)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        invoice_dict = self.invoice_entity.to_dict()
        self.assertIsInstance(invoice_dict, dict)
        expected_keys = [
            "invoice_id", "order_id", "customer_id", "date", "due_date",
            "amount", "status", "payment_terms", "currency", "tax_amount",
            "discount_amount", "shipping_amount", "subtotal", "total",
            "notes", "payment_method", "billing_address"
        ]
        for key in expected_keys:
            self.assertIn(key, invoice_dict)

    def test_generate_batch(self):
        """Test batch generation."""
        batch_size = 5
        invoices = self.invoice_entity.generate_batch(count=batch_size)
        self.assertEqual(len(invoices), batch_size)
        for invoice in invoices:
            self.assertIsInstance(invoice, dict)
            self.assertIn("invoice_id", invoice)
            self.assertIn("order_id", invoice)
            self.assertIn("amount", invoice)
            self.assertIn("date", invoice)
            self.assertIn("status", invoice)

    def test_reset(self):
        """Test reset functionality."""
        # Get initial values
        initial_invoice_id = self.invoice_entity.invoice_id
        initial_order_id = self.invoice_entity.order_id
        
        # Reset the entity
        self.invoice_entity.reset()
        
        # Get new values
        new_invoice_id = self.invoice_entity.invoice_id
        new_order_id = self.invoice_entity.order_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_invoice_id, new_invoice_id)
        self.assertNotEqual(initial_order_id, new_order_id)


if __name__ == "__main__":
    unittest.main() 