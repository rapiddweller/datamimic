# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Property cache utility for entity properties.

This module provides a utility class for caching entity properties.
"""

import functools
from collections.abc import Callable


def property_cache(func: Callable) -> Callable:
    """Decorator for caching property values.

    This decorator caches the result of a property getter method and returns the cached value
    on subsequent calls until the cache is reset.

    Args:
        func: The property getter method to cache

    Returns:
        A wrapped function that caches the result
    """
    cache_name = func.__name__

    @functools.wraps(func)
    def wrapper(self):
        if cache_name not in self.field_cache:
            # Generate a new value and store it in the cache
            value = func(self)
            self.field_cache[cache_name] = value
        return self.field_cache[cache_name]

    return wrapper
