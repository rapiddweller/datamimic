# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import shutil
from pathlib import Path

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


def test_checked_in_descriptor_pins_the_documented_range(tmp_path: Path) -> None:
    descriptor = tmp_path / "increment_end_exclusive.xml"
    shutil.copy(DESCRIPTOR, descriptor)
    captured = run(RunRequest(descriptor_path=descriptor, test_mode=True)).captured
    ids = {name: [int(row["id"]) for row in rows] for name, rows in captured.items()}
    assert ids["ids"] == [1, 2, 3, 4]
    assert ids["stepped"] == [1, 3]
    # Exhaustion is defined: 6 rows requested, only 4 exist below end=5, and the run succeeds.
    assert ids["exhausted"] == [1, 2, 3, 4]
