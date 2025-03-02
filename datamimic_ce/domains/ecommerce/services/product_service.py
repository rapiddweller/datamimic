# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product service module.

This module provides business logic services for e-commerce product data.
"""

import json
from typing import Any, Dict, List, Optional

from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator


class ProductService:
    """Service for e-commerce product operations.

    This class provides methods for generating and operating on product data,
    including creating products, filtering products, and formatting outputs.
    """

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        min_price: float = 0.99,
        max_price: float = 9999.99,
        dataset: Optional[str] = None,
    ):
        """Initialize the ProductService.

        Args:
            class_factory_util: A utility for creating class instances
            locale: Locale code for localization
            min_price: Minimum product price
            max_price: Maximum product price
            dataset: Optional dataset code (country code)
        """
        self._generator = ProductGenerator(
            class_factory_util=class_factory_util,
            locale=locale,
            min_price=min_price,
            max_price=max_price,
            dataset=dataset,
        )

    def create_product(self) -> Dict[str, Any]:
        """Create a single product.

        Returns:
            A dictionary containing product data
        """
        return self._generator.generate_product()

    def create_products(
        self,
        count: int = 100,
        category: Optional[str] = None,
        condition: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Create multiple products.

        Args:
            count: Number of products to generate
            category: Optional category filter
            condition: Optional condition filter
            min_price: Optional minimum price
            max_price: Optional maximum price

        Returns:
            A list of dictionaries containing product data
        """
        return self._generator.generate_products(
            count=count,
            category=category,
            condition=condition,
            min_price=min_price,
            max_price=max_price,
        )

    def get_product_categories(self) -> List[str]:
        """Get a list of available product categories.

        Returns:
            A list of product categories
        """
        return self._generator.get_available_categories()

    def filter_products_by_category(
        self, products: List[Dict[str, Any]], category: str
    ) -> List[Dict[str, Any]]:
        """Filter products by category.

        Args:
            products: List of product dictionaries
            category: Category to filter by

        Returns:
            Filtered list of products
        """
        return [product for product in products if product["category"] == category]

    def filter_products_by_price_range(
        self, products: List[Dict[str, Any]], min_price: float, max_price: float
    ) -> List[Dict[str, Any]]:
        """Filter products by price range.

        Args:
            products: List of product dictionaries
            min_price: Minimum price
            max_price: Maximum price

        Returns:
            Filtered list of products
        """
        return [
            product for product in products
            if min_price <= product["price"] <= max_price
        ]

    def format_products_for_csv(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format products for CSV export.

        This flattens nested structures and converts complex types to strings for CSV export.

        Args:
            products: List of product dictionaries

        Returns:
            List of flattened product dictionaries suitable for CSV export
        """
        formatted_products = []
        
        for product in products:
            flat_product = {}
            for key, value in product.items():
                if isinstance(value, (dict, list)):
                    flat_product[key] = json.dumps(value)
                else:
                    flat_product[key] = value
            formatted_products.append(flat_product)
        
        return formatted_products

    def format_products_for_database(
        self, products: List[Dict[str, Any]], format_type: str = "sql"
    ) -> List[Dict[str, Any]]:
        """Format products for database export.

        Args:
            products: List of product dictionaries
            format_type: Type of database format ("sql" or "nosql")

        Returns:
            List of product dictionaries formatted for database export
        """
        formatted_products = []
        
        for product in products:
            if format_type.lower() == "sql":
                # For SQL databases, flatten nested structures
                flat_product = {}
                for key, value in product.items():
                    if isinstance(value, (dict, list)):
                        flat_product[key] = json.dumps(value)
                    else:
                        flat_product[key] = value
                formatted_products.append(flat_product)
            else:
                # For NoSQL databases, keep the structure as is
                formatted_products.append(product)
        
        return formatted_products