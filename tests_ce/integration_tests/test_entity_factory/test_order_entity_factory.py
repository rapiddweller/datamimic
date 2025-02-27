# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import unittest

from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestOrderEntityFactory(unittest.TestCase):
    """Integration tests for the OrderEntity factory."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()

    def test_get_order_entity_default(self):
        """Test getting an OrderEntity with default parameters."""
        order_entity = self.class_factory_util.get_order_entity()
        
        # Verify the entity type and basic properties
        self.assertEqual(order_entity._locale, "en")
        self.assertEqual(order_entity._min_products, 1)
        self.assertEqual(order_entity._max_products, 10)
        self.assertEqual(order_entity._min_product_price, 0.99)
        self.assertEqual(order_entity._max_product_price, 999.99)
        self.assertIsNone(order_entity._dataset)
        
        # Verify that the entity can generate data
        order = order_entity.to_dict()
        self.assertIsInstance(order, dict)
        self.assertIn("order_id", order)
        self.assertIn("user_id", order)
        self.assertIn("product_list", order)
        self.assertIn("total_amount", order)
        self.assertIn("date", order)
        self.assertIn("status", order)

        # Verify the product list has the correct number of products
        self.assertGreaterEqual(len(order["product_list"]), order_entity._min_products)
        self.assertLessEqual(len(order["product_list"]), order_entity._max_products)

    def test_get_order_entity_with_params(self):
        """Test getting an OrderEntity with custom parameters."""
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        order_entity = self.class_factory_util.get_order_entity(
            locale="de",
            min_products=2,
            max_products=5,
            min_product_price=10.00,
            max_product_price=500.00,
            start_date=start_date,
            end_date=end_date,
            dataset="test_dataset"
        )
        
        # Verify the custom parameters were applied
        self.assertEqual(order_entity._locale, "de")
        self.assertEqual(order_entity._min_products, 2)
        self.assertEqual(order_entity._max_products, 5)
        self.assertEqual(order_entity._min_product_price, 10.00)
        self.assertEqual(order_entity._max_product_price, 500.00)
        self.assertEqual(order_entity._start_date, start_date)
        self.assertEqual(order_entity._end_date, end_date)
        self.assertEqual(order_entity._dataset, "test_dataset")
        
        # Verify the entity generates data with custom parameters
        order = order_entity.to_dict()
        self.assertIsInstance(order, dict)
        self.assertGreaterEqual(len(order["product_list"]), 2)
        self.assertLessEqual(len(order["product_list"]), 5)
        # Verify order date is within the specified range
        self.assertGreaterEqual(order["date"], start_date)
        self.assertLessEqual(order["date"], end_date)

    def test_get_order_entity_batch_generation(self):
        """Test batch generation using factory-created OrderEntity."""
        order_entity = self.class_factory_util.get_order_entity()
        
        # Generate a batch of orders
        batch_size = 10
        orders = order_entity.generate_batch(count=batch_size)
        
        # Verify the batch size and order structure
        self.assertEqual(len(orders), batch_size)
        for order in orders:
            self.assertIsInstance(order, dict)
            self.assertIn("order_id", order)
            self.assertIn("user_id", order)
            self.assertIn("product_list", order)
            self.assertIn("total_amount", order)
            self.assertIn("date", order)
            self.assertIn("status", order)

    def test_order_entity_reset(self):
        """Test resetting a factory-created OrderEntity."""
        order_entity = self.class_factory_util.get_order_entity()
        
        # Get initial values
        initial_order_id = order_entity.order_id
        initial_user_id = order_entity.user_id
        
        # Reset the entity
        order_entity.reset()
        
        # Get new values
        new_order_id = order_entity.order_id
        new_user_id = order_entity.user_id
        
        # Values should be different after reset
        self.assertNotEqual(initial_order_id, new_order_id)
        self.assertNotEqual(initial_user_id, new_user_id)


if __name__ == "__main__":
    unittest.main() 