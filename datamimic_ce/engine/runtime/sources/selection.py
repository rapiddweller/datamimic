# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Iterable, Iterator
from random import Random
from typing import TypeVar

from datamimic_ce.domains.common.sampling import cumulated_index
from datamimic_ce.engine.dsl.enums.distribution_enums import SourceDistribution
from datamimic_ce.engine.io.api import DataSourcePagination

T = TypeVar("T")


def unique_values(pool: Iterable[T], rng: Random) -> list[T]:
    """Return distinct pool items in random order."""
    seen: set = set()
    distinct: list[T] = []
    for item in pool:
        key = tuple(sorted(item.items())) if isinstance(item, dict) else item
        if key not in seen:
            seen.add(key)
            distinct.append(item)
    rng.shuffle(distinct)
    return distinct


def unique_value_iter(pool: Iterable[T], rng: Random, label: str) -> Iterator[T]:
    """Yield distinct pool items, then report exhaustion."""
    distinct = unique_values(pool, rng)
    yield from distinct
    raise ValueError(f"Cannot generate more than {len(distinct)} unique values for {label}")


def get_shuffled_data_with_cyclic(
    data: Iterable[T], pagination: DataSourcePagination | None, cyclic: bool | None, seed: int
) -> list[T]:
    """Return a seeded shuffled window, optionally cycling through the source."""
    source_len = len(list(data))
    if source_len == 0:
        return []

    if pagination is None:
        start_idx = 0
        end_idx = len(list(data))
    else:
        start_idx = pagination.skip
        end_idx = pagination.skip + pagination.limit

    if not cyclic:
        end_idx = min(end_idx, source_len)

    current_seed = seed + int(start_idx / source_len)
    res: list[T] = []
    while len(res) <= end_idx - start_idx or len(res) < (start_idx % source_len) + end_idx - start_idx:
        shuffle_data = list(data)
        Random(current_seed).shuffle(shuffle_data)
        res.extend(shuffle_data)
        current_seed += 1

    start_idx_cap = start_idx % source_len
    return res[start_idx_cap : start_idx_cap + end_idx - start_idx]


def get_distributed_data(
    data: Iterable[T],
    pagination: DataSourcePagination | None,
    cyclic: bool | None,
    seed: int,
    distribution: SourceDistribution,
) -> list[T]:
    """Apply the selected runtime row distribution to a loaded pool."""
    if distribution == SourceDistribution.CUMULATED:
        return get_cumulated_data(data, pagination, seed)
    return get_shuffled_data_with_cyclic(data, pagination, cyclic, seed)


def get_unique_data(data: Iterable[T], pagination: DataSourcePagination | None, seed: int, label: str) -> list[T]:
    """Return a seeded, paginated distinct selection; fail if the pool is too small."""
    distinct = unique_values(data, Random(seed))
    if pagination is None:
        return distinct
    end = pagination.skip + pagination.limit
    if end > len(distinct):
        raise ValueError(f"Cannot generate {end} unique values for {label}: only {len(distinct)} distinct available")
    return distinct[pagination.skip : end]


def get_cumulated_data(data: Iterable[T], pagination: DataSourcePagination | None, seed: int) -> list[T]:
    """Return a paginated seeded draw sequence sampled with replacement."""
    rows = list(data)
    source_len = len(rows)
    if source_len == 0:
        return []

    if pagination is None:
        start_idx, end_idx = 0, source_len
    else:
        start_idx = pagination.skip
        end_idx = pagination.skip + pagination.limit
    span = end_idx - start_idx

    rng = Random(seed)
    picks = [rows[cumulated_index(rng, source_len - 1)] for _ in range(start_idx + span)]
    return picks[start_idx:]
