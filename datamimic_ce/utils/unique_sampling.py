# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Iterable, Iterator
from random import Random
from typing import Any


def unique_values(pool: Iterable[Any], rng: Random) -> list[Any]:
    """Return the items of ``pool`` distinct and in random order (sampling without
    replacement). Single source of truth for ``unique="true"`` dedupe + shuffle.

    Duplicate items are collapsed (dict rows compared by their items, scalars directly),
    so the result is genuinely distinct even when the pool has duplicates.
    """
    seen: set = set()
    distinct: list = []
    for item in pool:
        key = tuple(sorted(item.items())) if isinstance(item, dict) else item
        if key not in seen:
            seen.add(key)
            distinct.append(item)
    rng.shuffle(distinct)
    return distinct


def unique_value_iter(pool: Iterable[Any], rng: Random, label: str) -> Iterator[Any]:
    """Iterator form of :func:`unique_values` for per-call consumers (``<key values>``,
    ``<variable source>``). Exhaustion (more requested than distinct available) raises a
    clear error rather than silently under-generating."""
    distinct = unique_values(pool, rng)
    yield from distinct
    raise ValueError(f"Cannot generate more than {len(distinct)} unique values for {label}")
