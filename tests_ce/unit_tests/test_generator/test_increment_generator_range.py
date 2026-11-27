# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import shutil
from pathlib import Path

import pytest

from datamimic_ce.domains.shared.literal_generators.numeric.increment_generator import IncrementGenerator
from datamimic_ce.engine.runtime.api import run
from datamimic_ce.engine.runtime.contracts import RunRequest

DESCRIPTOR = Path(__file__).with_name("increment_end_exclusive.xml")


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


def test_end_is_exclusive_when_it_is_off_the_step_sequence() -> None:
    # Equivalence class: step > 1 and (end - start) not a multiple of step.
    # Negative control: the old rule (value + step <= end) gave [1, 3] and dropped 5.
    assert _values(IncrementGenerator(1, 6, 2)) == [1, 3, 5]


def test_exhausted_generator_stays_exhausted() -> None:
    generator = IncrementGenerator(1, 6, 2)
    assert _values(generator) == [1, 3, 5]
    for _ in range(3):
        with pytest.raises(StopIteration):
            generator.generate()


def test_start_at_or_beyond_end_is_empty() -> None:
    assert _values(IncrementGenerator(5, 5)) == []
    assert _values(IncrementGenerator(7, 5, 2)) == []
    # Old rule: 4 + 2 > 5, so the only value below end was dropped.
    assert _values(IncrementGenerator(4, 5, 2)) == [4]


def test_paged_range_off_the_step_sequence() -> None:
    # Pages of (1,6,2): rows 1,3,5. Pages of two rows tile the range without overlap or gap.
    pages = []
    for skip in (0, 2, 4):
        generator = IncrementGenerator(1, 6, 2)
        generator.add_pagination(skip, 2)
        pages.append(_values(generator))
    assert pages == [[1, 3], [5], []]


def test_checked_in_descriptor_pins_the_documented_range(tmp_path: Path) -> None:
    descriptor = tmp_path / "increment_end_exclusive.xml"
    shutil.copy(DESCRIPTOR, descriptor)
    captured = run(RunRequest(descriptor_path=descriptor, test_mode=True)).captured
    ids = {name: [int(row["id"]) for row in rows] for name, rows in captured.items()}
    assert ids["ids"] == [1, 2, 3, 4]
    assert ids["stepped"] == [1, 3]
    assert ids["stepped_off_end"] == [1, 3, 5]
    assert ids["exhausted_stepped"] == [1, 3, 5]
    # Exhaustion is defined: 6 rows requested, only 4 exist below end=5, and the run succeeds.
    assert ids["exhausted"] == [1, 2, 3, 4]
