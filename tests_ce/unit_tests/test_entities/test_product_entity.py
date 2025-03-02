# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from unittest.mock import patch

from datamimic_ce.entities.product_entity import ProductEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestProductEntity(unittest.TestCase):
    """Test cases for the ProductEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.product_entity = ProductEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of ProductEntity."""
        self.assertEqual(self.product_entity._locale, "en")
        self.assertEqual(self.product_entity._min_price, 0.99)
        self.assertEqual(self.product_entity._max_price, 9999.99)
        self.assertIsNone(self.product_entity._dataset)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        product_entity = ProductEntity(
            self.class_factory_util,
            locale="de",
            min_price=5.99,
            max_price=499.99,
            dataset="test_dataset"
        )
        self.assertEqual(product_entity._locale, "de")
        self.assertEqual(product_entity._min_price, 5.99)
        self.assertEqual(product_entity._max_price, 499.99)
        self.assertEqual(product_entity._dataset, "test_dataset")

    def test_product_id_generation(self):
        """Test product ID generation."""
        product_id = self.product_entity.product_id
        self.assertTrue(product_id.startswith("PROD-"))
        self.assertEqual(len(product_id), 15)  # "PROD-" + 10 hex chars

    def test_name_generation(self):
        """Test product name generation."""
        # Mock the category and brand to ensure consistent test results
        with patch.object(ProductEntity, 'category', return_value="ELECTRONICS"):
            with patch.object(ProductEntity, 'brand', return_value="TechPro"):
                name = self.product_entity.name
                self.assertIsInstance(name, str)
                self.assertGreater(len(name), 0)

    def test_price_generation(self):
        """Test price generation."""
        price = self.product_entity.price
        self.assertIsInstance(price, float)
        self.assertGreaterEqual(price, self.product_entity._min_price)
        self.assertLessEqual(price, self.product_entity._max_price)

    def test_category_generation(self):
        """Test category generation."""
        category = self.product_entity.category
        self.assertIn(category, ProductEntity.PRODUCT_CATEGORIES)

    def test_brand_generation(self):
        """Test brand generation."""
        brand = self.product_entity.brand
        self.assertIn(brand, ProductEntity.PRODUCT_BRANDS)

    def test_sku_generation(self):
        """Test SKU generation."""
        sku = self.product_entity.sku
        self.assertIsInstance(sku, str)
        
        # SKU format should be: first 3 chars of brand - first 3 chars of category - 6 digits
        # Extract parts of the SKU
        parts = sku.split("-")
        self.assertEqual(len(parts), 3)
        
        # First part should be 3 characters (brand prefix)
        self.assertEqual(len(parts[0]), 3)
        # Second part should be 3 characters (category prefix)
        self.assertEqual(len(parts[1]), 3)
        # Third part should be 6 digits
        self.assertEqual(len(parts[2]), 6)
        self.assertTrue(parts[2].isdigit())

    def test_condition_generation(self):
        """Test condition generation."""
        condition = self.product_entity.condition
        self.assertIn(condition, ProductEntity.PRODUCT_CONDITIONS)

    def test_availability_generation(self):
        """Test availability generation."""
        availability = self.product_entity.availability
        self.assertIn(availability, ProductEntity.PRODUCT_AVAILABILITY)

    def test_currency_generation(self):
        """Test currency generation."""
        currency = self.product_entity.currency
        self.assertIn(currency, ProductEntity.CURRENCY_CODES)

    def test_weight_generation(self):
        """Test weight generation."""
        weight = self.product_entity.weight
        self.assertIsInstance(weight, float)
        self.assertGreaterEqual(weight, 0.1)
        self.assertLessEqual(weight, 50.0)

    def test_dimensions_generation(self):
        """Test dimensions generation."""
        dimensions = self.product_entity.dimensions
        self.assertIsInstance(dimensions, str)
        parts = dimensions.split(" x ")
        self.assertEqual(len(parts), 3)
        # Check that each part is a number followed by " cm"
        for part in parts[:2]:
            value = float(part)
            self.assertGreaterEqual(value, 1.0)
            self.assertLessEqual(value, 200.0)
        # Check the last part which includes " cm"
        value = float(parts[2].split(" ")[0])
        self.assertGreaterEqual(value, 1.0)
        self.assertLessEqual(value, 200.0)
        self.assertTrue(parts[2].endswith(" cm"))

    def test_color_generation(self):
        """Test color generation."""
        color = self.product_entity.color
        self.assertIsInstance(color, str)
        self.assertGreater(len(color), 0)

    def test_rating_generation(self):
        """Test rating generation."""
        rating = self.product_entity.rating
        self.assertIsInstance(rating, (float, int))
        self.assertGreaterEqual(rating, 1.0)
        self.assertLessEqual(rating, 5.0)

    def test_tags_generation(self):
        """Test tags generation."""
        tags = self.product_entity.tags
        self.assertIsInstance(tags, list)
        self.assertGreater(len(tags), 0)
        for tag in tags:
            self.assertIsInstance(tag, str)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        product_dict = self.product_entity.to_dict()
        self.assertIsInstance(product_dict, dict)
        expected_keys = [
            "product_id", "name", "description", "price", "category",
            "brand", "sku", "condition", "availability", "currency",
            "weight", "dimensions", "color", "rating", "tags"
        ]
        for key in expected_keys:
            self.assertIn(key, product_dict)

    def test_generate_batch(self):
        """Test batch generation."""
        batch_size = 5
        products = self.product_entity.generate_batch(count=batch_size)
        self.assertEqual(len(products), batch_size)
        for product in products:
            self.assertIsInstance(product, dict)
            self.assertIn("product_id", product)
            self.assertIn("name", product)
            self.assertIn("price", product)

    def test_reset(self):
        """Test reset functionality."""
        # Get initial values
        initial_product_id = self.product_entity.product_id
        initial_name = self.product_entity.name
        
        # Reset the entity
        self.product_entity.reset()
        
        # Get new values
        new_product_id = self.product_entity.product_id
        new_name = self.product_entity.name
        
        # Values should be different after reset
        self.assertNotEqual(initial_product_id, new_product_id)
        self.assertNotEqual(initial_name, new_name)


if __name__ == "__main__":
    unittest.main() 