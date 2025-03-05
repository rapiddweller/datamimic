# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest

from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestProductEntityFactory(unittest.TestCase):
    """Integration tests for the ProductEntity factory."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()

    def test_get_product_entity_default(self):
        """Test getting a ProductEntity with default parameters."""
        product_entity = self.class_factory_util.get_product_entity()
        
        # Verify the entity type and basic properties
        self.assertEqual(product_entity._locale, "en")
        self.assertEqual(product_entity._min_price, 0.99)
        self.assertEqual(product_entity._max_price, 9999.99)
        self.assertIsNone(product_entity._dataset)
        
        # Verify that the entity can generate data
        product = product_entity.to_dict()
        self.assertIsInstance(product, dict)
        self.assertIn("product_id", product)
        self.assertIn("name", product)
        self.assertIn("price", product)
        self.assertIn("category", product)
        self.assertIn("brand", product)

    def test_get_product_entity_with_params(self):
        """Test getting a ProductEntity with custom parameters."""
        product_entity = self.class_factory_util.get_product_entity(
            locale="de",
            min_price=5.99,
            max_price=499.99,
            dataset="test_dataset"
        )
        
        # Verify the custom parameters were applied
        self.assertEqual(product_entity._locale, "de")
        self.assertEqual(product_entity._min_price, 5.99)
        self.assertEqual(product_entity._max_price, 499.99)
        self.assertEqual(product_entity._dataset, "test_dataset")
        
        # Verify the entity can generate data with custom parameters
        product = product_entity.to_dict()
        self.assertIsInstance(product, dict)
        self.assertGreaterEqual(product["price"], 5.99)
        self.assertLessEqual(product["price"], 499.99)

    def test_get_product_entity_batch_generation(self):
        """Test batch generation using factory-created ProductEntity."""
        product_entity = self.class_factory_util.get_product_entity()
        
        # Generate a batch of products
        batch_size = 10
        products = product_entity.generate_batch(count=batch_size)
        
        # Verify the batch size and product structure
        self.assertEqual(len(products), batch_size)
        for product in products:
            self.assertIsInstance(product, dict)
            self.assertIn("product_id", product)
            self.assertIn("name", product)
            self.assertIn("price", product)
            self.assertIn("category", product)
            self.assertIn("brand", product)

    def test_product_entity_reset(self):
        """Test resetting a factory-created ProductEntity."""
        product_entity = self.class_factory_util.get_product_entity()
        
        # Get initial values
        initial_product_id = product_entity.product_id
        initial_name = product_entity.name
        
        # Reset the entity
        product_entity.reset()
        
        # Get new values
        new_product_id = product_entity.product_id
        new_name = product_entity.name
        
        # Values should be different after reset
        self.assertNotEqual(initial_product_id, new_product_id)
        self.assertNotEqual(initial_name, new_name)


if __name__ == "__main__":
    unittest.main() 