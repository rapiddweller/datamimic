# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Property cache utility for entity properties.

This module provides a utility class for caching entity properties.
"""

import functools
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")  # Define a type variable for generic typing


class PropertyCache(Generic[T]):
    """A utility class for caching entity properties.

    This class provides a way to cache property values and reset them when needed.
    It is used to avoid recalculating expensive property values.
    """

    def __init__(self, generator_fn: Callable[..., T]):
        """Initialize the PropertyCache with a generator function.

        Args:
            generator_fn: A function that generates property values when called
        """
        self._generator_fn = generator_fn
        self._cached_value: T | None = None
        self._cached = False

    def get(self, *args, **kwargs) -> T | None:
        """Get the cached value, or generate a new one if not cached.

        Args:
            *args: Positional arguments to pass to the generator function
            **kwargs: Keyword arguments to pass to the generator function

        Returns:
            The cached or newly generated value
        """
        if not self._cached:
            self._cached_value = self._generator_fn(*args, **kwargs)
            self._cached = True
        return self._cached_value

    def reset(self) -> None:
        """Reset the cached value, forcing a new value to be generated on the next get() call."""
        self._cached = False
        self._cached_value = None

    def set(self, value: T) -> None:
        """Set the cached value directly.

        Args:
            value: The value to cache
        """
        self._cached_value = value
        self._cached = True


def property_cache(func: Callable) -> Callable:
    """Decorator for caching property values.

    This decorator caches the result of a property getter method and returns the cached value
    on subsequent calls until the cache is reset.

    Args:
        func: The property getter method to cache

    Returns:
        A wrapped function that caches the result
    """
    cache_name = f"_{func.__name__}_cache"

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, cache_name) or getattr(self, cache_name) is None:
            # Generate a new value and store it in the cache
            value = func(self, *args, **kwargs)
            setattr(self, cache_name, value)
        return getattr(self, cache_name)

    # Add a method to reset the cache
    def reset_cache(self):
        setattr(self, cache_name, None)

    # Attach the reset method to the wrapper function
    wrapper.reset_cache = reset_cache

    return wrapper
