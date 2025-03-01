# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from collections.abc import Callable, Sequence
from typing import Any, TypeVar

T = TypeVar("T")


class LabTestUtils:
    """Utility functions for lab test entity."""

    @staticmethod
    def weighted_choice(values: Sequence[str | tuple[str, float]]) -> str:
        """Choose a value from a list based on weights.

        Args:
            values: Sequence of values, potentially with weights

        Returns:
            A chosen value
        """
        if not values:
            return ""

        # Parse values and weights
        parsed_values = []
        for v in values:
            if isinstance(v, tuple) and len(v) == 2:
                # Already a tuple of (value, weight)
                parsed_values.append(v)
            else:
                # String that needs to be parsed
                parsed_values.append(LabTestUtils.parse_weighted_value(v))

        # Extract just the values and weights
        items = [v[0] for v in parsed_values]
        weights = [v[1] for v in parsed_values]

        # Choose a value based on weights
        return random.choices(items, weights=weights, k=1)[0]

    @staticmethod
    def parse_weighted_value(value: str | tuple[str, float]) -> tuple[str, float]:
        """Parse a weighted value from a CSV file.

        Format: "value,weight" or just "value" (default weight is 1)

        Args:
            value: The value to parse

        Returns:
            A tuple of (value, weight)
        """
        # If already a tuple, return it
        if isinstance(value, tuple) and len(value) == 2:
            return value

        # Otherwise, parse the string
        parts = value.split(",", 1)
        if len(parts) == 2:
            try:
                weight = float(parts[1])
                return parts[0], weight
            except ValueError:
                # If the weight is not a valid number, treat it as part of the value
                return value, 1.0
        return value, 1.0


class PropertyCache:
    """Cache for entity properties."""

    def __init__(self):
        """Initialize an empty property cache."""
        self._cache: dict[str, Any] = {}  # type: ignore

    def get(self, property_name: str, generator_func: Callable[[], T]) -> T:
        """Get a cached property or generate and cache it if not present.

        Args:
            property_name: The name of the property to get.
            generator_func: The function to generate the property value.

        Returns:
            The cached or newly generated property value.
        """
        if property_name not in self._cache:
            self._cache[property_name] = generator_func()
        return self._cache[property_name]

    def clear(self) -> None:
        """Clear the property cache."""
        self._cache.clear()
