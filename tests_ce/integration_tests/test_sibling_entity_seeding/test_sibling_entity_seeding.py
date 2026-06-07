# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Same-type sibling entity variables draw independent, reproducible streams.

When several ``<variable entity="...">`` of the *same* type appear in one
``<generate>`` under a ``<setup rngSeed>``, each variable must produce its own
field values — siblings must not collapse onto a single shared stream.

CE guarantees this structurally (no fix was required to add this gate):

* Each ``<variable entity="...">`` forks an INDEPENDENT child RNG from the
  model-wide root seed via ``SetupContext.derive_seeded_rng`` →
  ``spawn_rng(root_rng)`` (``variable_task.py:_get_entity_generator``). Every
  fork advances the root RNG, so siblings receive distinct seed material.
* Each variable instantiates its OWN entity service instance — there is no
  shared, mutably-bound generator cached across siblings.

This test locks that contract in:

* siblings without a per-variable seed draw independent streams,
* the whole model replays byte-identically across runs,
* per-variable ``rngSeed`` overrides are honoured (equal seed => equal stream,
  different seed => different stream), independent of sibling order.
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_MODEL = "sibling_entity_seeding.xml"


def _run() -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=_MODEL, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def _pairs(rows: list[dict], prefix: str) -> list[tuple]:
    """Per-row (given, family) tuples for the variable bound to ``prefix``."""
    return [(row[f"{prefix}_given"], row[f"{prefix}_family"]) for row in rows]


def test_siblings_draw_independent_streams() -> None:
    """Two seed-less same-type siblings must not collapse onto one shared stream."""
    rows = _run()["siblings"]
    assert rows, "expected the siblings block to produce rows"
    a, b = _pairs(rows, "a"), _pairs(rows, "b")
    assert a != b, "sibling entity variables must draw distinct streams, not identical values"
    # Stronger than 'the lists differ': no individual row may share both fields,
    # which would betray a shared per-row stream.
    assert all(av != bv for av, bv in zip(a, b, strict=True)), (
        "no row may have byte-identical fields across siblings"
    )


def test_model_replays_byte_identically() -> None:
    """The full seeded model must reproduce byte-identically across two runs."""
    assert _run() == _run(), "seeded model must replay byte-identically"


def test_equal_per_variable_seed_reproduces_same_stream() -> None:
    """Siblings with the same explicit ``rngSeed`` reproduce the same stream."""
    rows = _run()["overrides"]
    assert _pairs(rows, "p") == _pairs(rows, "q"), (
        "same per-variable rngSeed must reproduce the same stream"
    )


def test_different_per_variable_seed_differs() -> None:
    """A different explicit ``rngSeed`` yields a different stream."""
    rows = _run()["overrides"]
    assert _pairs(rows, "p") != _pairs(rows, "r"), (
        "a different per-variable rngSeed must yield a different stream"
    )
