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


def test_end_is_inclusive_without_pagination() -> None:
    assert _drain(IncrementGenerator(1, 5)) == [1, 2, 3, 4, 5]


def test_end_is_inclusive_with_step() -> None:
    assert _drain(IncrementGenerator(1, 5, 2)) == [1, 3, 5]
    assert _drain(IncrementGenerator(1, 6, 2)) == [1, 3, 5]


def test_first_and_middle_page() -> None:
    first = IncrementGenerator(1, 10)
    first.add_pagination(0, 3)
    assert _drain(first) == [1, 2, 3]
    middle = IncrementGenerator(1, 10)
    middle.add_pagination(3, 3)
    assert _drain(middle) == [4, 5, 6]


def test_last_partial_page_stops_at_end() -> None:
    generator = IncrementGenerator(1, 10)
    generator.add_pagination(9, 5)
    assert _drain(generator) == [10]


def test_end_exactly_on_page_boundary() -> None:
    generator = IncrementGenerator(1, 6)
    generator.add_pagination(3, 3)
    assert _drain(generator) == [4, 5, 6]


def test_page_past_end_is_empty() -> None:
    generator = IncrementGenerator(1, 5)
    generator.add_pagination(10, 3)
    assert _drain(generator) == []


def test_step_greater_than_one_pages_by_row() -> None:
    generator = IncrementGenerator(1, 100, 5)
    generator.add_pagination(2, 3)
    assert _drain(generator) == [11, 16, 21]


def test_repeated_pagination_does_not_accumulate() -> None:
    # Negative control: the old implementation shifted the start on every call and returned [].
    generator = IncrementGenerator(1, 10)
    generator.add_pagination(3, 3)
    generator.add_pagination(3, 3)
    assert _drain(generator) == [4, 5, 6]


def test_non_positive_step_rejected() -> None:
    with pytest.raises(ValueError):
        IncrementGenerator(1, 5, 0)
