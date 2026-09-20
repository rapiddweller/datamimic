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

Hand-written models: ``dsl_constructs_seeded.xml`` (non-entity DSL constructs) and
``script_globals_seeded.xml`` / ``script_globals_unseeded.xml`` (stdlib names inside script expressions),
``replay_all_seeded.xml`` (every literal generator except the DB-backed sequence table, plus supported
dynamic script globals, replayed across processes).

Regenerate the committed models after adding/removing an entity::

    python tests_ce/integration_tests/test_determinism_seed_scenarios/test_determinism_seed_scenarios.py
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.domains.domain_core.generator_registry import generator_namespace
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


def test_dsl_constructs_replay_identically() -> None:
    """Hand-written model exercising null_quota / values / type-fallback /
    nestedKey count-bounds replays byte-for-byte under <setup rngSeed>."""
    first = _run(_TEST_DIR, "dsl_constructs_seeded.xml")
    second = _run(_TEST_DIR, "dsl_constructs_seeded.xml")
    assert first, "expected dsl_constructs_seeded.xml to produce entity blocks"
    assert first == second


def test_seeded_script_globals_replay_identically() -> None:
    """random / uuid.uuid4 / datetime now+today / fake inside script expressions replay under
    <setup rngSeed>; the clock is the deterministic anchor; pass-through members keep working."""
    first = _run(_TEST_DIR, "script_globals_seeded.xml")["script_globals"]
    second = _run(_TEST_DIR, "script_globals_seeded.xml")["script_globals"]
    assert first == second
    assert {row["now"] for row in first} == {"2025-01-01T12:00:00"}
    assert {row["today"] for row in first} == {"2025-01-01"}
    assert {row["pd_now"] for row in first} == {"2025-01-01T12:00:00"}
    assert len({row["uuid_value"] for row in first}) == len(first)
    assert {(row["built_year"], row["now_type"], row["uuid_int"]) for row in first} == {(2020, "datetime", 5)}


def test_unseeded_script_globals_stay_random() -> None:
    first = _run(_TEST_DIR, "script_globals_unseeded.xml")["script_globals"]
    second = _run(_TEST_DIR, "script_globals_unseeded.xml")["script_globals"]
    assert [row["uuid_value"] for row in first] != [row["uuid_value"] for row in second]
    assert [row["rand_int"] for row in first] != [row["rand_int"] for row in second]


_REPO_ROOT = _TEST_DIR.parents[2]
_RUN_IN_FRESH_PROCESS = """
import json, sys
from pathlib import Path
from datamimic_ce.data_mimic_test import DataMimicTest
engine = DataMimicTest(test_dir=Path(sys.argv[1]), filename=sys.argv[2], capture_test_result=True)
engine.test_with_timer()
result = json.dumps(engine.capture_result(), default=str, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
print("RESULT" + result)
"""


def canonical_result_bytes(result: dict) -> bytes:
    serialized = json.dumps(result, default=str, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return serialized.encode("utf-8")


def _run_in_fresh_process(filename: str) -> dict:
    completed = subprocess.run(
        [sys.executable, "-c", _RUN_IN_FRESH_PROCESS, str(_TEST_DIR), filename],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        cwd=_REPO_ROOT,
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": str(_REPO_ROOT),
            "PYTHONUTF8": "1",
        },
    )
    result_line = next(line for line in completed.stdout.splitlines() if line.startswith("RESULT"))
    return json.loads(result_line.removeprefix("RESULT"))


def test_replay_model_covers_every_literal_generator() -> None:
    model = (_TEST_DIR / "replay_all_seeded.xml").read_text(encoding="utf-8")
    used = set(re.findall(r'generator="([A-Za-z]+Generator)', model))
    assert set(generator_namespace()) - {"SequenceTableGenerator"} == used


def test_every_seeded_path_replays_across_processes() -> None:
    """Two separate processes replay every literal generator and supported dynamic script globals
    identically under <setup rngSeed>."""
    first = _run_in_fresh_process("replay_all_seeded.xml")
    second = _run_in_fresh_process("replay_all_seeded.xml")
    assert first["literal"] and first["script"]
    assert canonical_result_bytes(first) == canonical_result_bytes(second)


def replay_all_seeded_hash() -> str:
    return hashlib.sha256(canonical_result_bytes(_run_in_fresh_process("replay_all_seeded.xml"))).hexdigest()


if __name__ == "__main__":
    for name, kwargs in SCENARIOS.items():
        (_TEST_DIR / name).write_text(build_all_entities_seeded_xml(**kwargs))
        print(f"Wrote {_TEST_DIR / name}")
