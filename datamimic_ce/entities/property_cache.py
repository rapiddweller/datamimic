# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Property cache utility for entities.

This module provides a utility class for caching properties in entity classes.
"""

from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class PropertyCache(Generic[T]):
    """A utility class for caching property values for entities.

    This class provides a simple way to cache property values to avoid
    regenerating them every time they are accessed.
    """

    def __init__(self) -> None:
        """Initialize a new PropertyCache."""
        self._cache: dict[str, Any] = {}

    def get_or_create(self, key: str, generator_func: Callable[[], T]) -> T:
        """Get a cached value or create it if it doesn't exist.

        Args:
            key: The key to look up in the cache
            generator_func: A function that generates the value if not found in cache

        Returns:
            The cached or newly generated value
        """
        if key not in self._cache:
            self._cache[key] = generator_func()
        return self._cache[key]

    def set(self, key: str, value: T) -> None:
        """Set a value in the cache.

        Args:
            key: The key to store the value under
            value: The value to store
        """
        self._cache[key] = value

    def get(self, key: str) -> T:
        """Get a value from the cache.

        Args:
            key: The key to look up

        Returns:
            The cached value

        Raises:
            KeyError: If the key is not in the cache
        """
        return self._cache[key]

    def has(self, key: str) -> bool:
        """Check if a key exists in the cache.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        return key in self._cache

    def delete(self, key: str) -> None:
        """Delete a value from the cache.

        Args:
            key: The key to delete

        Raises:
            KeyError: If the key is not in the cache
        """
        del self._cache[key]

    def clear(self) -> None:
        """Clear all values from the cache."""
        self._cache.clear()
