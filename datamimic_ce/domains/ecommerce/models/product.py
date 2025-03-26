# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product model.

This module provides a model for representing an e-commerce product.
"""

import random
from typing import Any

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator


class Product(BaseEntity):
    """Model for representing an e-commerce product.

    This class provides a model for generating realistic product data including
    product IDs, names, descriptions, prices, categories, and other product attributes.
    """

    def __init__(
        self,
        product_generator: ProductGenerator,
    ):
        """Initialize the Product model.
        Args:
            product_generator: Product generator
        """
        super().__init__()
        self._product_generator = product_generator

    @property
    @property_cache
    def product_id(self) -> str:
        """Get the product ID.

        Returns:
            A unique product ID
        """
        return "PROD" + "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=8))

    @property
    @property_cache
    def category(self) -> str:
        """Get the product category.

        Returns:
            A product category
        """
        return self._product_generator.get_product_data_by_data_type("product_categories")

    @property
    @property_cache
    def brand(self) -> str:
        """Get the product brand.

        Returns:
            A product brand
        """
        return self._product_generator.get_product_data_by_data_type("product_brands")

    @property
    @property_cache
    def name(self) -> str:
        """Get the product name.

        Returns:
            A product name based on category and brand
        """
        category = self.category
        brand = self.brand
        adjective = self._product_generator.get_product_data_by_data_type("product_adjectives")
        noun = self._product_generator.get_product_data_by_data_type(f"product_nouns_{category}")
        if not noun:
            noun = "Product"

        patterns = [
            f"{brand} {adjective} {noun}",
            f"{adjective} {noun} by {brand}",
            f"{brand} {noun}",
            f"{adjective} {brand} {noun}",
        ]
        return random.choice(patterns)

    @property
    @property_cache
    def description(self) -> str:
        """Get the product description.

        Returns:
            A detailed product description
        """
        name = self.name
        category = self.category
        # Get category features
        selected_features = self._product_generator.get_random_features(category, min_feature=2, max_feature=3)
        # Create description
        description = f"{name} - {', '.join(selected_features)}. "
        description += (
            f"This premium {category.lower().replace('_', ' ')} product offers exceptional quality and value. "
        )
        # Add random benefit
        description += self._product_generator.get_product_data_by_data_type("product_benefits")
        return description

    @property
    @property_cache
    def price(self) -> float:
        """Get the product price.

        Returns:
            A realistic product price
        """
        return self._product_generator.price_with_strategy()

    @price.setter
    def price(self, value: float) -> None:
        """Set the product price.

        Args:
            value: The price to set.
        """
        self._field_cache["price"] = value

    @property
    @property_cache
    def sku(self) -> str:
        """Get the product SKU.

        Returns:
            A Stock Keeping Unit identifier
        """
        # Format: BRAND-CATEGORY-RANDOM
        brand_code = self.brand[:3].upper()
        category_code = self.category[:3].upper()
        random_code = "".join(random.choices("0123456789", k=6))

        return f"{brand_code}-{category_code}-{random_code}"

    @property
    @property_cache
    def condition(self) -> str:
        """Get the product condition.

        Returns:
            A product condition (e.g., NEW, USED)
        """
        return self._product_generator.get_product_data_by_data_type("product_conditions")

    @property
    @property_cache
    def availability(self) -> str:
        """Get the product availability.

        Returns:
            A product availability status (e.g., IN_STOCK)
        """
        return self._product_generator.get_product_data_by_data_type("product_availability")

    @availability.setter
    def availability(self, value: str) -> None:
        """Set the product availability.

        Args:
            value: The availability status to set.
        """
        self._field_cache["availability"] = value

    @property
    @property_cache
    def currency(self) -> str:
        """Get the product currency.

        Returns:
            A currency code (e.g., USD)
        """
        return self._product_generator.get_product_data_by_data_type("currencies")

    @property
    @property_cache
    def weight(self) -> float:
        """Get the product weight in kg.

        Returns:
            A realistic product weight
        """
        return self._product_generator.get_random_weight(self.category)

    @property
    @property_cache
    def dimensions(self) -> str:
        """Get the product dimensions.

        Returns:
            Product dimensions in the format "length x width x height cm"
        """
        return self._product_generator.get_random_dimensions(self.category)

    @property
    @property_cache
    def color(self) -> str:
        """Get the product color.

        Returns:
            A color name
        """
        return self._product_generator.get_product_data_by_data_type("product_colors")

    @property
    @property_cache
    def rating(self) -> float:
        """Get the product rating.

        Returns:
            A rating between 1.0 and 5.0
        """
        # Weight the ratings to make higher ratings more common
        weights = [0.05, 0.1, 0.2, 0.3, 0.35]  # Probabilities for 1-5 stars
        rating = float(random.choices([1, 2, 3, 4, 5], weights=weights, k=1)[0])

        # Add decimal precision for half-star ratings
        if random.random() < 0.5:
            rating -= 0.5

        return max(1.0, rating)  # Ensure minimum rating of 1.0

    @property
    @property_cache
    def tags(self) -> list[str]:
        """Get the product tags.

        Returns:
            A list of relevant tags for the product
        """
        category = self.category

        # Base tags from category
        base_tags = [category.lower().replace("_", " ")]

        # Add brand as a tag
        base_tags.append(self.brand.lower())

        # Add condition as a tag if not NEW
        condition = self.condition
        if condition != "NEW":
            base_tags.append(condition.lower())

        # Select 2-4 random tags from the category
        selected_category_tags = self._product_generator.get_random_tags(category)

        # Combine all tags
        all_tags = base_tags + selected_category_tags

        # Add a popular/trending tag occasionally
        if random.random() < 0.2:
            trending_tags = ["bestseller", "trending", "popular", "new arrival", "limited edition", "sale"]
            all_tags.append(random.choice(trending_tags))

        return all_tags

    def to_dict(self) -> dict[str, Any]:
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
