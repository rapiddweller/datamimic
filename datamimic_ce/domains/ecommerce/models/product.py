# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product model.

This module provides a model for representing an e-commerce product.
"""

from pathlib import Path
from typing import Any

from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator
from datamimic_ce.domains.domain_core import BaseEntity
from datamimic_ce.domains.domain_core.property_cache import property_cache
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator

# NOTE: No dataset I/O in model; all loading done in ProductGenerator


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
    def dataset(self) -> str:
        return self._product_generator.dataset  #  reuse generator dataset when resolving CSV assets

    @property
    @property_cache
    def product_id(self) -> str:
        """Get the product ID.

        Returns:
            A unique product ID
        """
        #  use shared PrefixedIdGenerator for prefixed ID without separator
        from datamimic_ce.domains.common.literal_generators.prefixed_id_generator import PrefixedIdGenerator

        return PrefixedIdGenerator("PROD", "[A-Z0-9]{8}", separator="").generate()

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

        #  deterministic RNG via generator; avoid module random
        patterns = (
            f"{brand} {adjective} {noun}",
            f"{adjective} {noun} by {brand}",
            f"{brand} {noun}",
            f"{adjective} {brand} {noun}",
        )
        return self._product_generator.rng.choice(list(patterns))

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
        #  use common StringGenerator for numeric segment
        random_code = StringGenerator.rnd_str_from_regex("[0-9]{6}")

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
        # Delegate to generator helper for dataset/rng logic
        return self._product_generator.pick_rating(start=Path(__file__))

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
        tag = self._product_generator.maybe_pick_trending_tag(start=Path(__file__))
        if tag:
            all_tags.append(tag)

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
