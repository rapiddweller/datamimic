# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import unittest
from unittest.mock import patch

from datamimic_ce.entities.order_entity import OrderEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestOrderEntity(unittest.TestCase):
    """Test cases for the OrderEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.order_entity = OrderEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of OrderEntity."""
        self.assertEqual(self.order_entity._locale, "en")
        self.assertEqual(self.order_entity._min_products, 1)
        self.assertEqual(self.order_entity._max_products, 10)
        self.assertEqual(self.order_entity._min_product_price, 0.99)
        self.assertEqual(self.order_entity._max_product_price, 999.99)
        self.assertIsNone(self.order_entity._dataset)
        # Check that start_date and end_date are set correctly
        self.assertIsInstance(self.order_entity._start_date, datetime.datetime)
        self.assertIsInstance(self.order_entity._end_date, datetime.datetime)
        self.assertLess(self.order_entity._start_date, self.order_entity._end_date)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        order_entity = OrderEntity(
            self.class_factory_util,
            locale="de",
            min_products=2,
            max_products=5,
            min_product_price=10.00,
            max_product_price=500.00,
            start_date=start_date,
            end_date=end_date,
            dataset="test_dataset"
        )
        self.assertEqual(order_entity._locale, "de")
        self.assertEqual(order_entity._min_products, 2)
        self.assertEqual(order_entity._max_products, 5)
        self.assertEqual(order_entity._min_product_price, 10.00)
        self.assertEqual(order_entity._max_product_price, 500.00)
        self.assertEqual(order_entity._start_date, start_date)
        self.assertEqual(order_entity._end_date, end_date)
        self.assertEqual(order_entity._dataset, "test_dataset")

    def test_order_id_generation(self):
        """Test order ID generation."""
        order_id = self.order_entity.order_id
        self.assertTrue(order_id.startswith("ORD-"))
        self.assertEqual(len(order_id), 14)  # "ORD-" + 10 hex chars

    def test_user_id_generation(self):
        """Test user ID generation."""
        user_id = self.order_entity.user_id
        self.assertTrue(user_id.startswith("USER-"))
        self.assertEqual(len(user_id), 13)  # "USER-" + 8 hex chars

    def test_product_list_generation(self):
        """Test product list generation."""
        product_list = self.order_entity.product_list
        self.assertIsInstance(product_list, list)
        self.assertGreaterEqual(len(product_list), self.order_entity._min_products)
        self.assertLessEqual(len(product_list), self.order_entity._max_products)
        
        # Check that each product has the expected keys
        for product in product_list:
            self.assertIsInstance(product, dict)
            expected_keys = ["product_id", "name", "price", "quantity"]
            for key in expected_keys:
                self.assertIn(key, product)
            
            # Check that price and quantity are within expected ranges
            self.assertGreaterEqual(product["price"], self.order_entity._min_product_price)
            self.assertLessEqual(product["price"], self.order_entity._max_product_price)
            self.assertGreaterEqual(product["quantity"], 1)
            self.assertLessEqual(product["quantity"], 10)

    def test_total_amount_generation(self):
        """Test total amount generation."""
        total_amount = self.order_entity.total_amount
        self.assertIsInstance(total_amount, float)
        # Total amount should be positive
        self.assertGreater(total_amount, 0.0)

    def test_date_generation(self):
        """Test date generation."""
        date = self.order_entity.date
        self.assertIsInstance(date, datetime.datetime)
        self.assertGreaterEqual(date, self.order_entity._start_date)
        self.assertLessEqual(date, self.order_entity._end_date)

    def test_status_generation(self):
        """Test order status generation."""
        status = self.order_entity.status
        self.assertIn(status, OrderEntity.ORDER_STATUSES)

    def test_payment_method_generation(self):
        """Test payment method generation."""
        payment_method = self.order_entity.payment_method
        self.assertIn(payment_method, OrderEntity.PAYMENT_METHODS)

    def test_shipping_method_generation(self):
        """Test shipping method generation."""
        shipping_method = self.order_entity.shipping_method
        self.assertIn(shipping_method, OrderEntity.SHIPPING_METHODS)

    def test_shipping_address_generation(self):
        """Test shipping address generation."""
        shipping_address = self.order_entity.shipping_address
        self.assertIsInstance(shipping_address, dict)
        expected_keys = ["street", "city", "state", "postal_code", "country"]
        for key in expected_keys:
            self.assertIn(key, shipping_address)

    def test_billing_address_generation(self):
        """Test billing address generation."""
        billing_address = self.order_entity.billing_address
        self.assertIsInstance(billing_address, dict)
        expected_keys = ["street", "city", "state", "postal_code", "country"]
        for key in expected_keys:
            self.assertIn(key, billing_address)

    def test_currency_generation(self):
        """Test currency generation."""
        currency = self.order_entity.currency
        self.assertIn(currency, OrderEntity.CURRENCY_CODES)

    def test_tax_amount_generation(self):
        """Test tax amount generation."""
        tax_amount = self.order_entity.tax_amount
        self.assertIsInstance(tax_amount, float)
        # Tax amount should be non-negative
        self.assertGreaterEqual(tax_amount, 0.0)

    def test_shipping_amount_generation(self):
        """Test shipping amount generation."""
        # Define shipping methods and their expected cost ranges
        shipping_methods_and_costs = {
            "STANDARD": (5.0, 10.0),
            "EXPRESS": (15.0, 25.0),
            "OVERNIGHT": (25.0, 50.0),
            "TWO_DAY": (12.0, 20.0),
            "INTERNATIONAL": (30.0, 100.0),
            "LOCAL_PICKUP": (0.0, 0.0),
            "STORE_PICKUP": (0.0, 0.0),
            "FREIGHT": (50.0, 200.0),
            "DIGITAL_DELIVERY": (0.0, 0.0),
        }

        # Test each shipping method
        for method, (min_cost, max_cost) in shipping_methods_and_costs.items():
            # Create a simple test to verify the shipping costs for each method
            # We'll directly test the _generate_shipping_amount method with a mocked shipping_method
            
            # Create a new instance for this test to avoid side effects
            order = OrderEntity(self.class_factory_util)
            
            # Mock the shipping_method property
            shipping_method_property = property(lambda self: method)
            
            # Apply the mock using a context manager
            with patch.object(OrderEntity, 'shipping_method', shipping_method_property):
                # Run the test multiple times to ensure consistency
                for _ in range(5):
                    # Generate shipping amount
                    shipping_amount = order._generate_shipping_amount()
                    
                    # Verify shipping amount is a float
                    self.assertIsInstance(shipping_amount, float)
                    
                    # Verify shipping amount is within expected range
                    self.assertGreaterEqual(shipping_amount, min_cost)
                    self.assertLessEqual(shipping_amount, max_cost, 
                                        f"Shipping amount {shipping_amount} for method {method} exceeds max {max_cost}")

    def test_discount_amount_generation(self):
        """Test discount amount generation."""
        discount_amount = self.order_entity.discount_amount
        self.assertIsInstance(discount_amount, float)
        # Discount amount should be non-negative
        self.assertGreaterEqual(discount_amount, 0.0)

    def test_coupon_code_generation(self):
        """Test coupon code generation."""
        coupon_code = self.order_entity.coupon_code
        # Coupon code can be None or a string
        if coupon_code is not None:
            self.assertIsInstance(coupon_code, str)
            # Check that it starts with one of the expected prefixes
            self.assertTrue(any(coupon_code.startswith(prefix) for prefix in 
                               ["SAVE", "DISCOUNT", "SPECIAL", "PROMO", "DEAL"]))

    def test_notes_generation(self):
        """Test notes generation."""
        notes = self.order_entity.notes
        # Notes can be None or a string
        if notes is not None:
            self.assertIsInstance(notes, str)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        order_dict = self.order_entity.to_dict()
        self.assertIsInstance(order_dict, dict)
        expected_keys = [
            "order_id", "user_id", "product_list", "total_amount", "date",
            "status", "payment_method", "shipping_method", "shipping_address",
            "billing_address", "currency", "tax_amount", "shipping_amount",
            "discount_amount", "coupon_code", "notes"
        ]
        for key in expected_keys:
            self.assertIn(key, order_dict)

    def test_generate_batch(self):
        """Test batch generation."""
        batch_size = 5
        orders = self.order_entity.generate_batch(count=batch_size)
        self.assertEqual(len(orders), batch_size)
        for order in orders:
            self.assertIsInstance(order, dict)
            self.assertIn("order_id", order)
            self.assertIn("user_id", order)
            self.assertIn("product_list", order)
            self.assertIn("total_amount", order)
            self.assertIn("date", order)
            self.assertIn("status", order)

    def test_reset(self):
        """Test reset functionality."""
        # Get initial values
        initial_order_id = self.order_entity.order_id
        initial_user_id = self.order_entity.user_id
        
        # Reset the entity
        self.order_entity.reset()
        
        # Get new values
        new_order_id = self.order_entity.order_id
        new_user_id = self.order_entity.user_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_order_id, new_order_id)
        self.assertNotEqual(initial_user_id, new_user_id)


if __name__ == "__main__":
    unittest.main() 