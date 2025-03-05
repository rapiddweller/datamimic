# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import json
import unittest

from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestECommerceEntities(unittest.TestCase):
    """Integration tests for the e-commerce entities."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        
        # Create all e-commerce entities
        self.product_entity = self.class_factory_util.get_product_entity()
        self.order_entity = self.class_factory_util.get_order_entity()
        self.invoice_entity = self.class_factory_util.get_invoice_entity()
        self.payment_entity = self.class_factory_util.get_payment_entity()
        self.transaction_entity = self.class_factory_util.get_transaction_entity()

    def test_individual_entities(self):
        """Test that each entity can generate data individually."""
        # Test ProductEntity
        product = self.product_entity.to_dict()
        self.assertIsInstance(product, dict)
        self.assertIn("product_id", product)
        self.assertIn("name", product)
        self.assertIn("price", product)
        
        # Test OrderEntity
        order = self.order_entity.to_dict()
        self.assertIsInstance(order, dict)
        self.assertIn("order_id", order)
        self.assertIn("product_list", order)
        self.assertIn("total_amount", order)
        
        # Test InvoiceEntity
        invoice = self.invoice_entity.to_dict()
        self.assertIsInstance(invoice, dict)
        self.assertIn("invoice_id", invoice)
        self.assertIn("order_id", invoice)
        self.assertIn("amount", invoice)
        
        # Test PaymentEntity
        payment = self.payment_entity.to_dict()
        self.assertIsInstance(payment, dict)
        self.assertIn("payment_id", payment)
        self.assertIn("method", payment)
        self.assertIn("amount", payment)
        
        # Test TransactionEntity
        transaction = self.transaction_entity.to_dict()
        self.assertIsInstance(transaction, dict)
        self.assertIn("transaction_id", transaction)
        self.assertIn("amount", transaction)
        self.assertIn("type", transaction)

    def test_batch_generation(self):
        """Test batch generation for all entities."""
        batch_size = 10
        
        # Test ProductEntity batch generation
        products = self.product_entity.generate_batch(count=batch_size)
        self.assertEqual(len(products), batch_size)
        
        # Test OrderEntity batch generation
        orders = self.order_entity.generate_batch(count=batch_size)
        self.assertEqual(len(orders), batch_size)
        
        # Test InvoiceEntity batch generation
        invoices = self.invoice_entity.generate_batch(count=batch_size)
        self.assertEqual(len(invoices), batch_size)
        
        # Test PaymentEntity batch generation
        payments = self.payment_entity.generate_batch(count=batch_size)
        self.assertEqual(len(payments), batch_size)
        
        # Test TransactionEntity batch generation
        transactions = self.transaction_entity.generate_batch(count=batch_size)
        self.assertEqual(len(transactions), batch_size)

    def test_create_related_entities(self):
        """Test creating related entities that reference each other."""
        # Create a product
        product = self.product_entity.to_dict()
        
        # Create an order containing the product
        order = self.order_entity.to_dict()
        order["product_list"] = [product]  # Replace the generated product list with our product
        order["total_amount"] = product["price"]  # Update the total amount
        
        # Create an invoice for the order
        invoice = self.invoice_entity.to_dict()
        invoice["order_id"] = order["order_id"]  # Link to our order
        invoice["amount"] = order["total_amount"]  # Match the order amount
        
        # Create a payment for the invoice
        payment = self.payment_entity.to_dict()
        payment["invoice_id"] = invoice["invoice_id"]  # Link to our invoice
        payment["amount"] = invoice["amount"]  # Match the invoice amount
        
        # Create a transaction for the payment
        transaction = self.transaction_entity.to_dict()
        transaction["reference_id"] = payment["payment_id"]  # Link to our payment
        transaction["amount"] = payment["amount"]  # Match the payment amount
        
        # Verify the relationships
        self.assertEqual(order["product_list"][0]["product_id"], product["product_id"])
        self.assertEqual(order["total_amount"], product["price"])
        self.assertEqual(invoice["order_id"], order["order_id"])
        self.assertEqual(invoice["amount"], order["total_amount"])
        self.assertEqual(payment["invoice_id"], invoice["invoice_id"])
        self.assertEqual(payment["amount"], invoice["amount"])
        self.assertEqual(transaction["reference_id"], payment["payment_id"])
        self.assertEqual(transaction["amount"], payment["amount"])

    def test_complete_ecommerce_system(self):
        """Test creating a complete e-commerce system."""
        # Generate sample data
        products = self.product_entity.generate_batch(count=5)
        orders = self.order_entity.generate_batch(count=3)
        invoices = self.invoice_entity.generate_batch(count=3)
        payments = self.payment_entity.generate_batch(count=3)
        transactions = self.transaction_entity.generate_batch(count=3)
        
        # Create a complete e-commerce system
        e_commerce_system = {
            "products": products,
            "orders": orders,
            "invoices": invoices,
            "payments": payments,
            "transactions": transactions
        }
        
        # Verify the system structure
        self.assertEqual(len(e_commerce_system["products"]), 5)
        self.assertEqual(len(e_commerce_system["orders"]), 3)
        self.assertEqual(len(e_commerce_system["invoices"]), 3)
        self.assertEqual(len(e_commerce_system["payments"]), 3)
        self.assertEqual(len(e_commerce_system["transactions"]), 3)
        
        # Verify that the system can be serialized to JSON
        json_data = json.dumps(e_commerce_system, default=str)
        self.assertIsInstance(json_data, str)

        
        # Create an invoice entity with custom date range
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        custom_invoice_entity = self.class_factory_util.get_invoice_entity(
            start_date=start_date,
            end_date=end_date
        )
        invoice = custom_invoice_entity.to_dict()
        invoice_date = invoice["date"]
        self.assertGreaterEqual(invoice_date, start_date)
        self.assertLessEqual(invoice_date, end_date)

    def test_entity_reset(self):
        """Test resetting entities."""
        # Get initial values
        initial_product_id = self.product_entity.product_id
        initial_order_id = self.order_entity.order_id
        initial_invoice_id = self.invoice_entity.invoice_id
        initial_payment_id = self.payment_entity.payment_id
        initial_transaction_id = self.transaction_entity.transaction_id
        
        # Reset all entities
        self.product_entity.reset()
        self.order_entity.reset()
        self.invoice_entity.reset()
        self.payment_entity.reset()
        self.transaction_entity.reset()
        
        # Get new values
        new_product_id = self.product_entity.product_id
        new_order_id = self.order_entity.order_id
        new_invoice_id = self.invoice_entity.invoice_id
        new_payment_id = self.payment_entity.payment_id
        new_transaction_id = self.transaction_entity.transaction_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_product_id, new_product_id)
        self.assertNotEqual(initial_order_id, new_order_id)
        self.assertNotEqual(initial_invoice_id, new_invoice_id)
        self.assertNotEqual(initial_payment_id, new_payment_id)
        self.assertNotEqual(initial_transaction_id, new_transaction_id)

    def test_create_realistic_order_flow(self):
        """Test creating a realistic order flow with all entities."""
        # 1. Create a product
        product = self.product_entity.to_dict()
        
        # 2. Create an order with the product
        order = self.order_entity.to_dict()
        # Replace the product list with our single product
        order["product_list"] = [{
            "product_id": product["product_id"],
            "name": product["name"],
            "price": product["price"],
            "quantity": 2
        }]
        # Update the total amount
        order["total_amount"] = product["price"] * 2
        
        # 3. Create an invoice for the order
        invoice = self.invoice_entity.to_dict()
        invoice["order_id"] = order["order_id"]
        invoice["customer_id"] = order["user_id"]
        invoice["amount"] = order["total_amount"]
        invoice["date"] = order["date"]
        invoice["due_date"] = order["date"] + datetime.timedelta(days=30)
        
        # 4. Create a payment for the invoice
        payment = self.payment_entity.to_dict()
        payment["invoice_id"] = invoice["invoice_id"]
        payment["customer_id"] = invoice["customer_id"]
        payment["amount"] = invoice["amount"]
        payment["timestamp"] = invoice["date"] + datetime.timedelta(days=2)
        payment["status"] = "COMPLETED"
        
        # 5. Create a transaction for the payment
        transaction = self.transaction_entity.to_dict()
        transaction["reference_id"] = payment["payment_id"]
        transaction["amount"] = payment["amount"]
        transaction["timestamp"] = payment["timestamp"]
        transaction["type"] = "PURCHASE"
        transaction["status"] = "COMPLETED"
        
        # 6. Update the order and invoice status
        order["status"] = "COMPLETED"
        invoice["status"] = "PAID"
        
        # 7. Create a complete order flow
        order_flow = {
            "product": product,
            "order": order,
            "invoice": invoice,
            "payment": payment,
            "transaction": transaction
        }
        
        # 8. Verify the flow
        self.assertEqual(order["product_list"][0]["product_id"], product["product_id"])
        self.assertEqual(order["total_amount"], product["price"] * 2)
        self.assertEqual(invoice["order_id"], order["order_id"])
        self.assertEqual(invoice["amount"], order["total_amount"])
        self.assertEqual(payment["invoice_id"], invoice["invoice_id"])
        self.assertEqual(payment["amount"], invoice["amount"])
        self.assertEqual(transaction["reference_id"], payment["payment_id"])
        self.assertEqual(transaction["amount"], payment["amount"])
        self.assertEqual(order["status"], "COMPLETED")
        self.assertEqual(invoice["status"], "PAID")
        self.assertEqual(payment["status"], "COMPLETED")
        self.assertEqual(transaction["status"], "COMPLETED")


if __name__ == "__main__":
    unittest.main() 