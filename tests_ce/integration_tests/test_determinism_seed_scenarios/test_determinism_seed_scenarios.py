# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Determinism contract verified at the DSL level across three seeding scenarios.

The DSL seed hierarchy (most specific wins): ``<setup rngSeed>`` is the model-wide
root from which seed-less variables derive child RNGs; ``<variable rngSeed>``
overrides it for that block. This pins the three combinations the README's
"same seed + same model = byte-identical output" claim depends on:

1. ``seed_in_setup``        — setup seed only            -> two runs identical.
2. ``seed_setup_and_generator`` — setup seed + variable  -> identical, and the
   variable seed OVERRIDES the setup seed (proven by re-seeding the setup).
3. ``no_seed``              — no seed anywhere           -> two runs differ.
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(test_dir: Path, filename: str) -> dict:
    engine = DataMimicTest(test_dir=test_dir, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_seed_in_setup_is_deterministic() -> None:
    """A setup-level seed makes seed-less variables replay identically."""
    first = _run(_TEST_DIR, "seed_in_setup.xml")
    second = _run(_TEST_DIR, "seed_in_setup.xml")
    assert first, "expected at least one generated block"
    assert first == second


def test_seed_setup_and_generator_is_deterministic() -> None:
    first = _run(_TEST_DIR, "seed_setup_and_generator.xml")
    second = _run(_TEST_DIR, "seed_setup_and_generator.xml")
    assert first == second


def test_variable_seed_overrides_setup_seed(tmp_path: Path) -> None:
    """The variable's rngSeed wins over the setup seed.

    Re-run the same model with a *different* <setup rngSeed>: the block whose variable
    carries its own rngSeed must be unchanged, while the block that only derives
    from the setup seed must change.
    """
    model = (_TEST_DIR / "seed_setup_and_generator.xml").read_text()
    (tmp_path / "seed_42.xml").write_text(model)
    (tmp_path / "seed_777.xml").write_text(model.replace('rngSeed="42"', 'rngSeed="777"'))

    a = _run(tmp_path, "seed_42.xml")
    b = _run(tmp_path, "seed_777.xml")

    assert a["overridden"] == b["overridden"], "variable rngSeed must override the setup seed"
    assert a["derived"] != b["derived"], "a seed-less variable must follow the setup seed"


def test_no_seed_is_random() -> None:
    """With no seed at all, two runs must differ (wall-clock seeded)."""
    first = _run(_TEST_DIR, "no_seed.xml")
    second = _run(_TEST_DIR, "no_seed.xml")
    assert first != second
