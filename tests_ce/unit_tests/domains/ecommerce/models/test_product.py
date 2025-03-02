# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Unit tests for the Product model.

This module contains tests for the Product model functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from datamimic_ce.domains.ecommerce.models.product import Product


class TestProduct(unittest.TestCase):
    """Test cases for the Product model."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_class_factory_util = MagicMock()
        self.product = Product(class_factory_util=self.mock_class_factory_util)

    def test_product_initialization(self):
        """Test that a Product can be initialized with default parameters."""
        self.assertIsInstance(self.product, Product)
        self.assertEqual(self.product._min_price, 0.99)
        self.assertEqual(self.product._max_price, 9999.99)

    def test_product_id_generation(self):
        """Test that a product ID is generated correctly."""
        product_id = self.product.product_id
        self.assertIsNotNone(product_id)
        self.assertTrue(product_id.startswith("PROD-"))
        self.assertEqual(len(product_id), 13)  # "PROD-" + 8 characters

    @patch("datamimic_ce.domains.ecommerce.models.product.ProductDataLoader.get_product_categories")
    def test_category_property(self, mock_get_categories):
        """Test that a category is selected correctly."""
        # Mock the data loader to return test categories
        mock_get_categories.return_value = [("ELECTRONICS", 1.0), ("CLOTHING", 1.0)]
        
        # Create a new product with the mocked data loader
        product = Product(class_factory_util=self.mock_class_factory_util)
        
        # Get the category
        category = product.category
        
        # Verify that the category is one of the expected values
        self.assertIn(category, ["ELECTRONICS", "CLOTHING"])
        
        # Verify that the data loader was called with the correct parameters
        mock_get_categories.assert_called_once_with(None)

    @patch("datamimic_ce.domains.ecommerce.models.product.ProductDataLoader.get_product_brands")
    def test_brand_property(self, mock_get_brands):
        """Test that a brand is selected correctly."""
        # Mock the data loader to return test brands
        mock_get_brands.return_value = [("ACME", 1.0), ("TechPro", 1.0)]
        
        # Create a new product with the mocked data loader
        product = Product(class_factory_util=self.mock_class_factory_util)
        
        # Get the brand
        brand = product.brand
        
        # Verify that the brand is one of the expected values
        self.assertIn(brand, ["ACME", "TechPro"])
        
        # Verify that the data loader was called with the correct parameters
        mock_get_brands.assert_called_once_with(None)

    def test_price_property(self):
        """Test that a price is generated within the specified range."""
        # Test with default price range
        price = self.product.price
        self.assertGreaterEqual(price, 0.99)
        self.assertLessEqual(price, 9999.99)
        
        # Test with custom price range
        product = Product(
            class_factory_util=self.mock_class_factory_util,
            min_price=10.0,
            max_price=100.0,
        )
        price = product.price
        self.assertGreaterEqual(price, 10.0)
        self.assertLessEqual(price, 100.0)

    def test_to_dict_method(self):
        """Test that the to_dict method returns all required fields."""
        product_dict = self.product.to_dict()
        
        # Check that all required fields are present
        required_fields = [
            "product_id", "name", "description", "price", "category",
            "brand", "sku", "condition", "availability", "currency",
            "weight", "dimensions", "color", "rating", "tags",
        ]
        
        for field in required_fields:
            self.assertIn(field, product_dict)
            self.assertIsNotNone(product_dict[field])

    def test_reset_method(self):
        """Test that the reset method clears all cached values."""
        # First, access some properties to cache them
        product_id = self.product.product_id
        name = self.product.name
        
        # Reset the product
        self.product.reset()
        
        # Verify that the cached values are cleared (internal variables are None)
        self.assertIsNone(self.product._product_id)
        self.assertIsNone(self.product._name)
        
        # Verify that accessing the properties again generates new values
        new_product_id = self.product.product_id
        self.assertIsNotNone(new_product_id)
        
        # The product_id should be different after reset
        self.assertNotEqual(product_id, new_product_id)

    def test_generate_batch(self):
        """Test that generate_batch returns the correct number of products."""
        # Generate a batch of products
        batch = self.product.generate_batch(count=5)
        
        # Verify that the batch contains the correct number of products
        self.assertEqual(len(batch), 5)
        
        # Verify that each product in the batch has all required fields
        required_fields = [
            "product_id", "name", "description", "price", "category",
            "brand", "sku", "condition", "availability", "currency",
        ]
        
        for product in batch:
            for field in required_fields:
                self.assertIn(field, product)
                self.assertIsNotNone(product[field])


if __name__ == "__main__":
    unittest.main()