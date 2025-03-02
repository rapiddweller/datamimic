# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from typing import TypeVar

T = TypeVar("T")


def weighted_choice(items: list[T | tuple[T, float]]) -> T:
    """Choose an item from a list, with optional weights.

    Args:
        items: A list of items, where each item is either a value or a tuple of (value, weight).

    Returns:
        A randomly selected item.
    """
    if not items:
        raise ValueError("Cannot choose from an empty list")

    # Check if items have weights
    if isinstance(items[0], tuple) and len(items[0]) == 2:
        # Items are (value, weight) tuples
        values, weights = zip(*items, strict=False)
        return random.choices(values, weights=weights, k=1)[0]
    else:
        # Items are just values
        return random.choice(items)


def random_subset(items: list[T], min_size: int = 1, max_size: int | None = None) -> list[T]:
    """Select a random subset of items.

    Args:
        items: The list of items to select from.
        min_size: The minimum size of the subset.
        max_size: The maximum size of the subset. If None, defaults to len(items).

    Returns:
        A randomly selected subset of items.
    """
    if not items:
        return []

    if max_size is None:
        max_size = len(items)

    # Ensure min_size and max_size are valid
    min_size = max(0, min(min_size, len(items)))
    max_size = max(min_size, min(max_size, len(items)))

    # Choose a random size for the subset
    subset_size = random.randint(min_size, max_size)

    # Select a random subset
    return random.sample(items, subset_size)


def random_bool(true_probability: float = 0.5) -> bool:
    """Generate a random boolean value.

    Args:
        true_probability: The probability of returning True (between 0 and 1).

    Returns:
        A random boolean value.
    """
    return random.random() < true_probability


def random_int_in_range(min_value: int, max_value: int) -> int:
    """Generate a random integer in the specified range.

    Args:
        min_value: The minimum value (inclusive).
        max_value: The maximum value (inclusive).

    Returns:
        A random integer between min_value and max_value.
    """
    return random.randint(min_value, max_value)


def random_float_in_range(min_value: float, max_value: float) -> float:
    """Generate a random float in the specified range.

    Args:
        min_value: The minimum value (inclusive).
        max_value: The maximum value (inclusive).

    Returns:
        A random float between min_value and max_value.
    """
    return random.uniform(min_value, max_value)


def random_element_with_exclusions(items: list[T], exclusions: list[T]) -> T:
    """Choose a random element from a list, excluding specified elements.

    Args:
        items: The list of items to choose from.
        exclusions: The list of items to exclude.

    Returns:
        A randomly selected item that is not in the exclusions list.
    """
    if not items:
        raise ValueError("Cannot choose from an empty list")

    # Filter out excluded items
    valid_items = [item for item in items if item not in exclusions]

    if not valid_items:
        raise ValueError("No valid items to choose from after applying exclusions")

    return random.choice(valid_items)


def shuffle_list(items: list[T]) -> list[T]:
    """Shuffle a list in place and return it.

    Args:
        items: The list to shuffle.

    Returns:
        The shuffled list.
    """
    result = items.copy()
    random.shuffle(result)
    return result
