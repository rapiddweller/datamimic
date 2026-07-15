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

Fixtures covered
----------------
* ``source.csv``         — plain single-column CSV (ids 0..11)
* ``data/people.ent.csv`` — entity CSV (id,name; 12 rows)
* ``data/people.json``   — JSON array of objects (id,name; 12 entries)
* cascading generate     — outer <generate> + <nestedKey> reading people.ent.csv
* SQLite                 — database source (ids 0..11)
"""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_FILE_ORDER = [str(i) for i in range(12)]
_FILE_NAMES = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Hank", "Ivy", "Jack", "Karen", "Leo"]


def _order(filename: str) -> list[str]:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return [row["id"] for row in engine.capture_result()["rows"]]


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


# ---------------------------------------------------------------------------
# plain CSV (source.csv)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# .ent.csv (entity CSV — data/people.ent.csv, columns id,name)
# ---------------------------------------------------------------------------


def test_ent_csv_seeded_replays_identically() -> None:
    """`<setup rngSeed>` on an .ent.csv source: two runs byte-identical and shuffled."""
    first = _run("ent_csv_seeded.xml")["rows"]
    second = _run("ent_csv_seeded.xml")["rows"]
    assert first == second, "seeded .ent.csv read must replay identically"
    ids_first = [r["id"] for r in first]
    assert sorted(ids_first) == sorted(_FILE_ORDER), "every source row must appear exactly once"
    assert ids_first != _FILE_ORDER, "must be genuinely shuffled (not file order)"


def test_ent_csv_unseeded_is_non_deterministic() -> None:
    """Without a setup seed, two .ent.csv random reads differ."""
    r1 = [row["id"] for row in _run("ent_csv_unseeded.xml")["rows"]]
    r2 = [row["id"] for row in _run("ent_csv_unseeded.xml")["rows"]]
    assert r1 != r2, "unseeded .ent.csv reads must differ between runs"


# ---------------------------------------------------------------------------
# .json (JSON array — data/people.json, keys id,name)
# ---------------------------------------------------------------------------


def test_json_seeded_replays_identically() -> None:
    """`<setup rngSeed>` on a .json source: two runs byte-identical and shuffled."""
    first = _order("json_seeded.xml")
    second = _order("json_seeded.xml")
    assert first == second, "seeded .json read must replay identically"
    assert sorted(first) == sorted(_FILE_ORDER), "every source row must appear exactly once"
    assert first != _FILE_ORDER, "must be genuinely shuffled (not file order)"


def test_json_unseeded_is_non_deterministic() -> None:
    """Without a setup seed, two .json random reads differ."""
    assert _order("json_unseeded.xml") != _order("json_unseeded.xml")


# ---------------------------------------------------------------------------
# Cascading generate: outer <generate> + <nestedKey source=people.ent.csv>
# ---------------------------------------------------------------------------


def test_cascade_seeded_replays_identically() -> None:
    """`<setup rngSeed>` makes the full nested structure deterministic.

    The outer generate produces 3 rows each with a ``children`` list of 4
    people drawn from ``data/people.ent.csv`` with ``distribution="random"``.
    With a seed, both the per-row shuffle and the row ordering replay
    identically across two independent runs.
    """
    first = _run("cascade_seeded.xml")["outer"]
    second = _run("cascade_seeded.xml")["outer"]
    assert first == second, "seeded cascading generate must replay identically"
    # Sanity: inner list is genuinely shuffled (not just file order)
    child_names_0 = [c["name"] for c in first[0]["children"]]
    assert child_names_0 != _FILE_NAMES[:4], "children must be shuffled, not file order"


def test_cascade_unseeded_is_non_deterministic() -> None:
    """Without a setup seed, two cascading-generate runs differ."""
    first = _run("cascade_unseeded.xml")["outer"]
    second = _run("cascade_unseeded.xml")["outer"]
    assert first != second, "unseeded cascading generate must differ between runs"


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------

_SQLITE_ROW_IDS = [str(i) for i in range(12)]


def test_sqlite_seeded_random_read_replays_identically() -> None:
    """`<setup rngSeed>` makes a random SQLite source read reproducible — and still shuffled."""
    first = _order("sqlite_seeded.xml")
    second = _order("sqlite_seeded.xml")
    assert first == second, "seeded sqlite random read must replay identically"
    assert sorted(first) == sorted(_SQLITE_ROW_IDS), "every source row must appear exactly once"
    assert first != _SQLITE_ROW_IDS, "it must be genuinely shuffled, not table order"


def test_sqlite_unseeded_random_read_is_non_deterministic() -> None:
    """Without a setup seed, two random SQLite reads of the same source differ."""
    assert _order("sqlite_unseeded.xml") != _order("sqlite_unseeded.xml")
