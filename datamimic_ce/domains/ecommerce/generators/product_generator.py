# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product generator module.

This module provides a generator for e-commerce product data.
"""

from typing import Any, Dict, List, Optional

from datamimic_ce.domains.ecommerce.data_loaders.product_loader import ProductDataLoader
from datamimic_ce.domains.ecommerce.models.product import Product


class ProductGenerator:
    """Generator for e-commerce product data.

    This class provides methods to generate individual products or batches
    of products with realistic data.
    """

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        min_price: float = 0.99,
        max_price: float = 9999.99,
        dataset: Optional[str] = None,
    ):
        """Initialize the ProductGenerator.

        Args:
            class_factory_util: A utility for creating class instances
            locale: Locale code for localization
            min_price: Minimum product price
            max_price: Maximum product price
            dataset: Optional dataset code (country code)
        """
        self._class_factory_util = class_factory_util
        self._locale = locale
        self._min_price = min_price
        self._max_price = max_price
        self._dataset = dataset
        
        # Create the product model for generating data
        self._product = Product(
            class_factory_util=class_factory_util,
            locale=locale,
            min_price=min_price,
            max_price=max_price,
            dataset=dataset,
        )

    def generate_product(self) -> Dict[str, Any]:
        """Generate a single product.

        Returns:
            A dictionary containing product data
        """
        # Generate product data and reset for next generation
        product_data = self._product.to_dict()
        self._product.reset()
        return product_data

    def generate_products(
        self,
        count: int = 100,
        category: Optional[str] = None,
        condition: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Generate multiple products.

        Args:
            count: Number of products to generate
            category: Optional category filter
            condition: Optional condition filter
            min_price: Optional minimum price
            max_price: Optional maximum price

        Returns:
            A list of dictionaries containing product data
        """
        products = []
        
        # Use the batch generation method
        batch = self._product.generate_batch(count)
        
        # Apply filters if specified
        for product in batch:
            # Category filter
            if category and product["category"] != category:
                continue
                
            # Condition filter
            if condition and product["condition"] != condition:
                continue
                
            # Price filters
            if min_price is not None and product["price"] < min_price:
                continue
                
            if max_price is not None and product["price"] > max_price:
                continue
                
            products.append(product)
        
        return products

    def get_available_categories(self) -> List[str]:
        """Get a list of available product categories.

        Returns:
            A list of product categories
        """
        categories = ProductDataLoader.get_product_categories(self._dataset)
        return [category for category, _ in categories]

    def get_available_brands(self) -> List[str]:
        """Get a list of available product brands.

        Returns:
            A list of product brands
        """
        brands = ProductDataLoader.get_product_brands(self._dataset)
        return [brand for brand, _ in brands]

    def get_available_conditions(self) -> List[str]:
        """Get a list of available product conditions.

        Returns:
            A list of product conditions
        """
        conditions = ProductDataLoader.get_product_conditions(self._dataset)
        return [condition for condition, _ in conditions]

    def get_available_currencies(self) -> List[str]:
        """Get a list of available currencies.

        Returns:
            A list of currency codes
        """
        currencies = ProductDataLoader.get_currencies(self._dataset)
        return [currency for currency, _ in currencies]