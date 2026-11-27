# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import pytest

from datamimic_ce.domains.shared.literal_generators.numeric.increment_generator import IncrementGenerator


def _drain(generator: IncrementGenerator) -> list[int]:
    values: list[int] = []
    while len(values) < 100:
        try:
            values.append(generator.generate())
        except StopIteration:
            break
    return values


def _page(skip: int, limit: int, end: int = 10, step: int = 1, start: int = 1) -> list[int]:
    generator = IncrementGenerator(start, end, step)
    generator.add_pagination(skip, limit)
    return _drain(generator)


def test_first_page() -> None:
    assert _page(0, 3) == [1, 2, 3]


def test_middle_page() -> None:
    assert _page(3, 3) == [4, 5, 6]


def test_last_partial_page_stops_at_end() -> None:
    assert _page(7, 5) == [8, 9]


def test_page_ending_exactly_at_the_end() -> None:
    assert _page(3, 6) == [4, 5, 6, 7, 8, 9]


def test_page_past_end_is_empty() -> None:
    assert _page(20, 3) == []


def test_step_greater_than_one_pages_by_row() -> None:
    assert _page(2, 3, end=100, step=5) == [11, 16, 21]


def test_step_greater_than_one_with_end_off_the_sequence_pages_by_row() -> None:
    # (1,6,2) holds the rows 1,3,5. Negative control: the old rule dropped 5 from the last page.
    assert _page(0, 2, end=6, step=2) == [1, 3]
    assert _page(2, 2, end=6, step=2) == [5]
    assert _page(4, 2, end=6, step=2) == []


def test_repeated_pagination_does_not_accumulate() -> None:
    # Negative control: the old implementation shifted the start on every call and returned [].
    generator = IncrementGenerator(1, 10)
    generator.add_pagination(3, 3)
    generator.add_pagination(3, 3)
    assert _drain(generator) == [4, 5, 6]


def test_non_positive_step_rejected() -> None:
    with pytest.raises(ValueError):
        IncrementGenerator(1, 5, 0)
