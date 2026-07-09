# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Memstore API extensions unblocking memstore/memstore.ben.xml (Benerator parity)."""

import shutil
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent


def test_wgt_ent_csv_reads_via_iterate():
    """'.wgt.ent.csv' despite the name is a normal headered CSV (test_id|flag|count), NOT the
    headerless value|weight '.wgt.csv' format - already readable via <iterate> today, verified
    directly rather than assumed. This is a regression test, not a fix."""
    engine = DataMimicTest(_dir, "test_wgt_ent_csv_iterate.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["test_file"]
    assert len(rows) == 3
    assert {r["test_id"] for r in rows} == {"1", "2", "3"}
    assert {r["flag"] for r in rows} == {"true", "false"}


def test_memstore_sum_skips_non_numeric_cells():
    """Benerator-lenient aggregation, end to end: a CSV-sourced count column carrying a stray
    non-numeric placeholder ('n/a') must not abort the sum - 5 + skip + 7 = 12."""
    engine = DataMimicTest(_dir, "test_memstore_sum_lenient.xml", capture_test_result=True)
    engine.test_with_timer()
    assert engine.capture_result()["result"][0]["total"] == 12


def test_memstore_accessible_by_id_before_and_after_execute():
    """mem is bound into the script namespace at <memstore> registration time, not only inside
    <execute> - so a <key script="mem...."> resolves it whether it runs BEFORE or AFTER any
    <execute> statement in the descriptor (proves this isn't riding eval_namespace's diff-
    writeback side effect, which would only work in the "after" ordering)."""
    engine = DataMimicTest(_dir, "test_memstore_variable_script_access.xml", capture_test_result=True)
    engine.test_with_timer()
    result = engine.capture_result()
    assert result["before_execute"][0]["count"] == 5
    assert result["after_execute"][0]["count"] == 5


def test_memstore_sum_feeds_a_subsequent_count():
    """mem.sumEntityColumn() inside <execute>, its result driving count="{totalCount}" on a later
    <generate>, and mem.entityCount() confirming it - the exact pipeline
    memstore/memstore.ben.xml uses. values="5,3,7" picks randomly per row (not one-of-each), so
    only the total's range is asserted, not an exact value - the point is internal consistency
    across the whole sum -> count -> generate -> recount pipeline."""
    engine = DataMimicTest(_dir, "test_memstore_sum_and_count.xml", capture_test_result=True)
    engine.test_with_timer()
    row = engine.capture_result()["result"][0]
    assert 9 <= row["totalCount"] <= 21  # 3 rows, each in {3,5,7}
    assert row["teCount"] == row["totalCount"]


def test_memstore_remove_not_existing_ids():
    """mem.removeNotExistingIds('t','id','ref',db) inside <execute> - an inner-join filter
    against a real RDBMS table. ref has ids {1,3}; mem has ids {1,2,3} - only 2 should be
    removed."""
    output_dir = _dir / "output"
    # sqlite relative paths resolve against the process CWD, not the descriptor dir - clean up
    # both the test's own dir (the documented convention elsewhere in this suite) and the repo
    # root (where it actually lands when pytest's CWD is the repo root).
    repo_root_db_dir = _dir.parents[2] / "db"
    local_db_dir = _dir / "db"
    for d in (output_dir, repo_root_db_dir, local_db_dir):
        shutil.rmtree(d, ignore_errors=True)
    try:
        engine = DataMimicTest(_dir, "test_memstore_remove_not_existing_ids.xml", capture_test_result=True)
        engine.test_with_timer()
        row = engine.capture_result()["result"][0]
        assert row["remaining_ids"] == [1, 3]
    finally:
        for d in (output_dir, repo_root_db_dir, local_db_dir):
            shutil.rmtree(d, ignore_errors=True)
