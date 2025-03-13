# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product model.

This module provides a model for representing an e-commerce product.
"""
from typing import Any, Dict, List

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.ecommerce.generators.product_generator_new import ProductGeneratorNew
from datamimic_ce.domains.ecommerce.utils.random_utils import generate_id


class ProductNew(BaseEntity):
    """Model for representing an e-commerce product.

    This class provides a model for generating realistic product data including
    product IDs, names, descriptions, prices, categories, and other product attributes.
    """

    def __init__(self, product_generator: ProductGeneratorNew):
        super().__init__()
        self._product_generator = product_generator

    @property
    @property_cache
    def product_data(self) -> Dict[str, Any]:
        return self._product_generator.get_random_product()

    @property
    @property_cache
    def product_id(self) -> str:
        """Get the product ID.

        Returns:
            A unique product ID
        """
        return self.product_data["product_id"]

    @property
    @property_cache
    def category(self) -> str:
        """Get the product category.

        Returns:
            A product category
        """
        return self.product_data["category"]

    @property
    @property_cache
    def brand(self) -> str:
        """Get the product brand.

        Returns:
            A product brand
        """
        return self.product_data["brand"]

    @property
    @property_cache
    def name(self) -> str:
        """Get the product name.

        Returns:
            A product name based on category and brand
        """
        return self.product_data["name"]

    @property
    @property_cache
    def description(self) -> str:
        """Get the product description.

        Returns:
            A detailed product description
        """
        return self.product_data["description"]

    @property
    @property_cache
    def price(self) -> float:
        """Get the product price.

        Returns:
            A realistic product price
        """
        return self.product_data["price"]

    @property
    @property_cache
    def sku(self) -> str:
        """Get the product SKU.

        Returns:
            A Stock Keeping Unit identifier
        """
        return self.product_data["sku"]

    @property
    @property_cache
    def condition(self) -> str:
        """Get the product condition.

        Returns:
            A product condition (e.g., NEW, USED)
        """
        return self.product_data["condition"]

    @property
    @property_cache
    def availability(self) -> str:
        """Get the product availability.

        Returns:
            A product availability status (e.g., IN_STOCK)
        """
        return self.product_data["availability"]

    @property
    @property_cache
    def currency(self) -> str:
        """Get the product currency.

        Returns:
            A currency code (e.g., USD)
        """
        return self.product_data["currency"]

    @property
    @property_cache
    def weight(self) -> float:
        """Get the product weight in kg.

        Returns:
            A realistic product weight
        """
        return self.product_data["weight"]

    @property
    @property_cache
    def dimensions(self) -> str:
        """Get the product dimensions.

        Returns:
            Product dimensions in the format "length x width x height cm"
        """
        return self.product_data["dimensions"]

    @property
    @property_cache
    def color(self) -> str:
        """Get the product color.

        Returns:
            A color name
        """
        return self.product_data["color"]

    @property
    @property_cache
    def rating(self) -> float:
        """Get the product rating.

        Returns:
            A rating between 1.0 and 5.0
        """
        return self.product_data["rating"]

    @property
    @property_cache
    def tags(self) -> List[str]:
        """Get the product tags.

        Returns:
            A list of relevant tags for the product
        """
        return self.product_data["tags"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the product to a dictionary.

        Returns:
            A dictionary representation of the product
        """
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "category": self.category,
            "brand": self.brand,
            "sku": self.sku,
            "condition": self.condition,
            "availability": self.availability,
            "currency": self.currency,
            "weight": self.weight,
            "dimensions": self.dimensions,
            "color": self.color,
            "rating": self.rating,
            "tags": self.tags,
        }