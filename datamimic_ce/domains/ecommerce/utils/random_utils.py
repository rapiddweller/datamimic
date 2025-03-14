# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Random utility functions for e-commerce data generation.

This module contains utility functions for generating random data for e-commerce entities.
"""

import random
from typing import Any, TypeVar, cast

T = TypeVar("T")  # Define a type variable for generic typing


def weighted_choice(options: list[tuple[T, float]]) -> T:
    """Choose an item from a list of options with weights.

    Args:
        options: A list of tuples containing items and their weights

    Returns:
        A randomly selected item based on weights
    """
    if not options:
        raise ValueError("Cannot choose from an empty list")

    items, weights = zip(*options, strict=False)
    return cast(T, random.choices(items, weights=weights, k=1)[0])


def price_with_strategy(min_price: float, max_price: float) -> float:
    """Generate a price using common pricing strategies.

    Args:
        min_price: Minimum price
        max_price: Maximum price

    Returns:
        A price following common pricing strategies like .99 endings
    """
    # Use different price points based on common retail pricing strategies
    price_points = [
        round(random.uniform(min_price, max_price), 2),  # Regular price
        round(random.uniform(max(min_price, 1.0), min(max_price, 100)), 99) / 100,  # $X.99 price
        round(random.uniform(max(min_price, 100), min(max_price, 1000)), 95) / 100,  # $X.95 price
        round(random.uniform(max(min_price, 1000), max_price), 0),  # Whole dollar price for expensive items
    ]

    price = random.choice(price_points)
    return max(min_price, min(price, max_price))  # Ensure price is between min_price and max_price


def generate_id(prefix: str, length: int = 10) -> str:
    """Generate a random ID with a prefix.

    Args:
        prefix: Prefix for the ID
        length: Length of the random part of the ID

    Returns:
        A random ID with the specified prefix
    """
    random_part = "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=length))
    return f"{prefix}-{random_part}"


def get_property_values_by_category(
    category: str, properties: dict[str, dict[str, list[Any]]], property_name: str, default: list[Any] = []
) -> list[Any]:
    """Get property values for a specific category.

    Args:
        category: The category to get properties for
        properties: Dictionary of properties by category
        property_name: The name of the property to get
        default: Default values if the property doesn't exist

    Returns:
        A list of property values for the category
    """
    category_properties = properties.get(category, {})
    return category_properties.get(property_name, default)
