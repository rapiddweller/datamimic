# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Determinism contract verified at the DSL level across three seeding scenarios.

Each scenario runs the FULL registry-driven model — every entity and a
representative scalar of every attribute and sub-structure — produced by the
shared ``build_all_entities_seeded_xml`` builder, so the contract is exercised
over the complete entity surface, not a hand-picked subset. Seeding is varied via
the builder's ``setup_seed`` / ``variable_seed`` knobs:

1. setup seed only        (``<setup rngSeed>``, no per-variable seed) -> identical.
2. setup + variable seed  (per-variable ``rngSeed`` overrides the setup root):
   the variable seed wins (re-seeding the setup leaves output unchanged), while a
   seed-less variable follows the setup seed.
3. no seed anywhere       -> two runs differ (wall-clock random).
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
from tests_ce.integration_tests.dsl_model_builder import build_all_entities_seeded_xml


def _run(tmp_path: Path, xml: str, name: str) -> dict:
    model = tmp_path / f"{name}.xml"
    model.write_text(xml)
    engine = DataMimicTest(test_dir=tmp_path, filename=model.name, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_setup_seed_makes_the_full_model_deterministic(tmp_path: Path) -> None:
    """`<setup rngSeed>` alone: every seed-less variable replays identically."""
    xml = build_all_entities_seeded_xml(setup_seed=42, variable_seed=None)
    first = _run(tmp_path, xml, "run_a")
    second = _run(tmp_path, xml, "run_b")
    assert first, "expected the full model to produce entity blocks"
    assert first == second


def test_variable_seed_overrides_setup_seed(tmp_path: Path) -> None:
    """A per-variable rngSeed wins over the setup seed; a seed-less one follows it."""
    overridden_42 = _run(tmp_path, build_all_entities_seeded_xml(setup_seed=42, variable_seed=99), "ov42")
    overridden_777 = _run(tmp_path, build_all_entities_seeded_xml(setup_seed=777, variable_seed=99), "ov777")
    assert overridden_42 == overridden_777, "variable rngSeed must override the setup seed (setup change ignored)"

    derived_42 = _run(tmp_path, build_all_entities_seeded_xml(setup_seed=42, variable_seed=None), "dv42")
    derived_777 = _run(tmp_path, build_all_entities_seeded_xml(setup_seed=777, variable_seed=None), "dv777")
    assert derived_42 != derived_777, "a seed-less variable must follow the setup seed (setup change shows)"


def test_no_seed_is_random(tmp_path: Path) -> None:
    """No setup seed and no per-variable seed: two runs of the full model differ."""
    xml = build_all_entities_seeded_xml(setup_seed=None, variable_seed=None)
    first = _run(tmp_path, xml, "run_a")
    second = _run(tmp_path, xml, "run_b")
    assert first != second
