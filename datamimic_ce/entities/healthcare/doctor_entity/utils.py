# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Utility functions for the doctor entity.
"""

import random
from collections.abc import Callable
from typing import Any, TypeVar, cast

T = TypeVar("T")


class PropertyCache:
    """Cache for entity properties.

    This class provides a simple cache for entity properties to avoid
    regenerating values that have already been generated.
    """

    def __init__(self):
        """Initialize the property cache."""
        self._cache: dict[str, Any] = {}

    def get(self, key: str, generator: Callable[[], T]) -> T:
        """Get a value from the cache, generating it if not present.

        Args:
            key: The cache key.
            generator: A function that generates the value if not in cache.

        Returns:
            The cached or newly generated value.
        """
        if key not in self._cache:
            self._cache[key] = generator()
        return cast(T, self._cache[key])

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()


def weighted_choice(values: list[str | tuple[str, float]]) -> str:
    """Select a value from a list based on weights.

    Args:
        values: A list of values, either as strings or as tuples of (value, weight).

    Returns:
        A randomly selected value based on weights.

    Raises:
        ValueError: If the input list is empty.
    """
    if not values:
        raise ValueError("Cannot select from an empty list")

    # Parse values and weights
    items_and_weights = [parse_weighted_value(v) if isinstance(v, str) else v for v in values]

    # Extract values and weights
    items = [item for item, _ in items_and_weights]
    weights = [weight for _, weight in items_and_weights]

    # Select a value based on weights
    return random.choices(items, weights=weights, k=1)[0]


def parse_weighted_value(value: str) -> tuple[str, float]:
    """Parse a string formatted as "value,weight" or just "value".

    Args:
        value: A string in the format "value,weight" or just "value".

    Returns:
        A tuple of (value, weight).
    """
    parts = value.split(",", 1)
    if len(parts) == 1:
        return parts[0], 1.0
    try:
        return parts[0], float(parts[1])
    except (ValueError, IndexError):
        return parts[0], 1.0


def generate_license_number() -> str:
    """Generate a random medical license number.

    Returns:
        A string representing a medical license number.
    """
    # Format: 2 letters followed by 6 digits
    letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    digits = "".join(random.choices("0123456789", k=6))
    return f"{letters}{digits}"


def generate_npi_number() -> str:
    """Generate a random National Provider Identifier (NPI) number.

    Returns:
        A string representing an NPI number.
    """
    # NPI is a 10-digit number
    return "".join(random.choices("0123456789", k=10))


def format_phone_number(number: str) -> str:
    """Format a phone number in the standard US format.

    Args:
        number: A 10-digit phone number.

    Returns:
        A formatted phone number string.
    """
    if len(number) != 10:
        return number
    return f"({number[:3]}) {number[3:6]}-{number[6:]}"


def generate_email(first_name: str, last_name: str) -> str:
    """Generate an email address based on a name.

    Args:
        first_name: The first name.
        last_name: The last name.

    Returns:
        An email address.
    """
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com"]
    domain = random.choice(domains)

    # Clean names
    first = first_name.lower().replace(" ", "")
    last = last_name.lower().replace(" ", "")

    # Different email formats
    formats = [
        f"{first}.{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}{last[0]}@{domain}",
        f"{first}_{last}@{domain}",
        f"{last}.{first}@{domain}",
    ]

    return random.choice(formats)
