# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from datamimic_ce.domains.shared.literal_generators.numeric.increment_generator import IncrementGenerator


def _values(generator: IncrementGenerator) -> list[int]:
    values: list[int] = []
    while True:
        try:
            values.append(generator.generate())
        except StopIteration:
            return values


def test_end_is_exclusive_with_unit_step() -> None:
    # Documented range: end=5 is never produced.
    assert _values(IncrementGenerator(1, 5)) == [1, 2, 3, 4]


def test_documented_range_with_step_greater_than_one() -> None:
    # Equivalence class: step > 1. Documented as 1, 3 for end=5.
    assert _values(IncrementGenerator(1, 5, 2)) == [1, 3]
