# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Determinism contract verified at the DSL level across three seeding scenarios.

Each scenario is a COMMITTED, reviewable DATAMIMIC DSL model — the FULL
registry-driven model (every entity + a representative scalar of every attribute
and sub-structure), produced by the shared ``build_all_entities_seeded_xml``
builder and checked in so a reviewer can read it top-to-bottom. A sync-check fails
if any committed model drifts from the builder, so they cannot rot.

The three models differ only in their seed wiring:

1. ``seed_in_setup.xml``           — ``<setup rngSeed>`` only        -> two runs identical.
2. ``seed_setup_and_generator.xml`` — ``<setup rngSeed>`` + per-variable ``rngSeed``
   (the variable seed overrides the setup root; a seed-less variable follows it).
3. ``no_seed.xml``                 — no seed anywhere               -> two runs differ.

Regenerate the committed models after adding/removing an entity::

    python tests_ce/integration_tests/test_determinism_seed_scenarios/test_determinism_seed_scenarios.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
from tests_ce.integration_tests.dsl_model_builder import build_all_entities_seeded_xml

_TEST_DIR = Path(__file__).resolve().parent

# Committed model -> the builder seeding that must reproduce it.
SCENARIOS = {
    "seed_in_setup.xml": {"setup_seed": 42, "variable_seed": None},
    "seed_setup_and_generator.xml": {"setup_seed": 42, "variable_seed": 99},
    "no_seed.xml": {"setup_seed": None, "variable_seed": None},
}


def _run(test_dir: Path, filename: str) -> dict:
    engine = DataMimicTest(test_dir=test_dir, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


@pytest.mark.parametrize("filename", SCENARIOS)
def test_committed_model_is_in_sync_with_builder(filename: str) -> None:
    """Each committed scenario model must equal what the builder produces today."""
    expected = build_all_entities_seeded_xml(**SCENARIOS[filename])
    assert (_TEST_DIR / filename).read_text() == expected, (
        f"{filename} is out of sync. Regenerate: "
        f"python tests_ce/integration_tests/test_determinism_seed_scenarios/test_determinism_seed_scenarios.py"
    )


def test_setup_seed_makes_the_full_model_deterministic() -> None:
    """`<setup rngSeed>` alone: every seed-less variable replays identically."""
    first = _run(_TEST_DIR, "seed_in_setup.xml")
    second = _run(_TEST_DIR, "seed_in_setup.xml")
    assert first, "expected the full model to produce entity blocks"
    assert first == second


def test_setup_and_generator_is_deterministic() -> None:
    first = _run(_TEST_DIR, "seed_setup_and_generator.xml")
    second = _run(_TEST_DIR, "seed_setup_and_generator.xml")
    assert first == second


def test_variable_seed_overrides_setup_seed(tmp_path: Path) -> None:
    """Re-seeding only the setup root leaves overridden variables unchanged.

    A per-variable rngSeed wins over `<setup rngSeed>` (output is unchanged when
    the setup seed changes), while a seed-less variable follows the setup seed
    (output changes). Both halves use the committed models as the canonical input,
    swapping only the setup seed for the comparison run.
    """

    def _reseeded(filename: str) -> dict:
        swapped = (_TEST_DIR / filename).read_text().replace('rngSeed="42"', 'rngSeed="777"', 1)
        (tmp_path / filename).write_text(swapped)
        return _run(tmp_path, filename)

    overridden = _run(_TEST_DIR, "seed_setup_and_generator.xml")
    assert overridden == _reseeded("seed_setup_and_generator.xml"), "variable rngSeed must override the setup seed"

    derived = _run(_TEST_DIR, "seed_in_setup.xml")
    assert derived != _reseeded("seed_in_setup.xml"), "a seed-less variable must follow the setup seed"


def test_no_seed_is_random() -> None:
    """No setup seed and no per-variable seed: two runs of the full model differ."""
    first = _run(_TEST_DIR, "no_seed.xml")
    second = _run(_TEST_DIR, "no_seed.xml")
    assert first != second


if __name__ == "__main__":
    for name, kwargs in SCENARIOS.items():
        (_TEST_DIR / name).write_text(build_all_entities_seeded_xml(**kwargs))
        print(f"Wrote {_TEST_DIR / name}")
