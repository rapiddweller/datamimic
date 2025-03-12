# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Product model.

This module provides a model for representing an e-commerce product.
"""
from typing import Any, Dict

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
    def product_id(self) -> str:
        """Get the product ID.

        Returns:
            A unique product ID
        """
        return generate_id("PROD", 8)

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