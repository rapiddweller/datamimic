# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# See LICENSE file for the full text of the license.

"""A literal <key generator="IntegerGenerator(...)"> under <setup rngSeed> replays deterministically."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str, gen: str = "g") -> list[dict]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()[gen]


def test_seeded_integer_generator_is_reproducible():
    a = [r["n"] for r in _run("int_generator_seeded.xml")]
    b = [r["n"] for r in _run("int_generator_seeded.xml")]
    assert a == b  # same seed -> same numbers (DATAMIMIC's core promise)
    assert all(1000 <= n <= 9999 for n in a)
