# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Utility functions for the Clinical Trial Entity.

This module provides utility functions for generating and manipulating clinical trial data.
"""

import random
import string
from collections.abc import Callable, Sequence
from typing import Any


class PropertyCache:
    """Cache for entity properties to avoid regenerating values."""

    def __init__(self) -> None:
        """Initialize an empty cache."""
        self._cache: dict[str, Any] = {}

    def get(self, key: str) -> Any:
        """Get a value from the cache.

        Args:
            key: The key to retrieve

        Returns:
            The cached value or None if not found
        """
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the cache.

        Args:
            key: The key to set
            value: The value to cache
        """
        self._cache[key] = value

    def get_or_create(self, key: str, creator_func: Callable[[], Any]) -> Any:
        """Get a value from the cache or create it if not present.
        
        Args:
            key: The key to retrieve
            creator_func: Function to call to create the value if not in cache
            
        Returns:
            The cached value or the newly created value
        """
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
            
        value = creator_func()
        self.set(key, value)
        return value

    def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()


def weighted_choice(values: Sequence[tuple[str, float | int]] | Sequence[str]) -> str:
    """Choose a value from a list with weights.

    Args:
        values: Sequence of values with weights or sequence of strings

    Returns:
        A randomly chosen value
    """
    if not values:
        raise ValueError("Cannot choose from an empty sequence")

    # If the values are already tuples of (value, weight), use them directly
    weighted_values = values if isinstance(values[0], tuple) else [parse_weighted_value(value) for value in values]

    # Extract values and weights
    choices, weights = zip(*weighted_values, strict=False)

    # Choose a random value based on weights
    return random.choices(choices, weights=weights, k=1)[0]


def parse_weighted_value(value: str | tuple[str, float]) -> tuple[str, float]:
    """Parse a weighted value from a CSV file.

    Args:
        value: The value to parse, potentially in the format "value,weight"

    Returns:
        A tuple of (value, weight)
    """
    # If already a tuple, return it
    if isinstance(value, tuple) and len(value) == 2:
        return value[0], float(value[1])  # Ensure weight is float

    # Otherwise, parse the string
    if isinstance(value, str) and "," in value:
        parts = value.rsplit(",", 1)
        if len(parts) == 2 and parts[1].strip().replace(".", "", 1).isdigit():
            return parts[0], float(parts[1])
    return value, 1.0


def generate_trial_id() -> str:
    """Generate a unique clinical trial identifier.

    Returns:
        A string in the format "NCT" followed by 8 digits
    """
    # Generate a random 8-digit number
    digits = ''.join(random.choices(string.digits, k=8))
    return f"NCT{digits}"
