# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Seeded random source reads replay identically; unseeded ones stay random.

``distribution="random"`` shuffles a data source. With ``<setup rngSeed>`` the
shuffle is derived from the run's root RNG, so the read order is reproducible
across runs (required for stable source-based pseudonymization). Without a setup
seed the order is non-deterministic — the privacy-maximized default.

These committed DSL fixtures read ``source.csv`` (ids 0..11).
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_FILE_ORDER = [str(i) for i in range(12)]


def _order(filename: str) -> list[str]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return [row["id"] for row in engine.capture_result()["rows"]]


def test_seeded_random_read_replays_identically() -> None:
    """`<setup rngSeed>` makes a random source read reproducible — and still shuffled."""
    first = _order("random_seeded.xml")
    second = _order("random_seeded.xml")
    assert first == second, "seeded random read must replay identically"
    assert sorted(first) == sorted(_FILE_ORDER), "every source row must appear exactly once"
    assert first != _FILE_ORDER, "it must be genuinely shuffled, not file order"


def test_unseeded_random_read_is_non_deterministic() -> None:
    """Without a setup seed, two random reads of the same source differ."""
    assert _order("random_unseeded.xml") != _order("random_unseeded.xml")
