# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""target="db.clear" empties a table once and keeps it; clear and drop reject every other shape with I928 (BC-4.0-016).

The models are DSL files next to this test; the RDBMS runs on SQLite. MongoDB drop and clear run in the
external-service tests."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from datamimic_ce.errors import IssueCode, OperationError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def _run(project_dir: Path, filename: str) -> dict:
    engine = DataMimicTest(test_dir=project_dir, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_clear_empties_one_table_and_keeps_the_others(project_dir):
    result = _run(project_dir, "clear_one_table.xml")
    assert result["items_left"] == []
    assert [row["id"] for row in result["kept_left"]] == [1]


def test_cleanup_followed_by_inserts_gives_the_same_rows_on_every_run(project_dir):
    first = _run(project_dir, "clear_then_insert.xml")["items_left"]
    second = _run(project_dir, "clear_then_insert.xml")["items_left"]
    assert [(row["id"], row["name"]) for row in first] == [(1, "n1"), (2, "n2"), (3, "n3")]
    assert second == first


def test_several_clears_run_in_document_order(project_dir):
    result = _run(project_dir, "clear_in_dependency_order.xml")
    assert result["parent_left"] == []
    assert result["child_left"] == []


def test_a_clear_reached_through_an_include_runs(project_dir):
    assert _run(project_dir, "clear_through_include.xml")["items_left"] == []


def test_clear_on_a_read_only_client_is_blocked_and_keeps_the_rows(project_dir):
    with pytest.raises(OperationError) as caught:
        _run(project_dir, "clear_read_only.xml")
    assert caught.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED
    with closing(sqlite3.connect(project_dir / "db" / "clear_ops_readonly.sqlite")) as connection:
        assert connection.execute("SELECT COUNT(*) FROM items").fetchone() == (1,)


def test_a_clear_before_a_file_export_leaves_the_exported_file_complete(project_dir):
    _run(project_dir, "clear_then_json_export.xml")
    (exported,) = list((project_dir / "output").rglob("exported.json"))
    assert [row["id"] for row in json.loads(exported.read_text(encoding="utf-8"))] == [1, 2, 3]


def _rows_left(project_dir: Path) -> int:
    with closing(sqlite3.connect(project_dir / "db" / "clear_ops_refused.sqlite")) as connection:
        return connection.execute("SELECT COUNT(*) FROM items").fetchone()[0]


@pytest.mark.parametrize(
    ("model", "reason"),
    [
        ("refused_call_syntax", "forbidden attributes: count"),
        ("refused_include_in_generate", "root-only operations"),
        ("refused_nested_include_in_generate", "root-only operations"),
    ],
)
def test_a_clear_that_would_repeat_is_refused_and_keeps_the_rows(project_dir: Path, model: str, reason: str):
    with pytest.raises(OperationError) as caught:
        _run(project_dir, f"{model}.xml")
    assert caught.value.issue_code is IssueCode.OPERATION_INTENT_INVALID
    assert reason in str(caught.value)
    assert _rows_left(project_dir) == 2


@pytest.mark.parametrize(
    ("model", "reason"),
    [
        ("with_count", "forbidden attributes: count"),
        ("with_source", "forbidden attributes: source, sourceEntity"),
        ("with_selector", "forbidden attributes: selector, source"),
        ("with_script", "forbidden attributes: script"),
        ("with_children", "forbidden attributes: children"),
        ("with_second_target", "forbidden attributes: otherTargets"),
        ("without_target_entity", "clear and drop require explicit targetEntity"),
        ("nested", "root-only operations"),
        ("drop_on_rdbms", "drop is supported only for MongoDB collections"),
        ("unknown_client", "target client 'nodb' is not configured"),
    ],
)
def test_an_invalid_clear_or_drop_fails_with_i928_before_any_database_access(
    project_dir: Path, model: str, reason: str
):
    with pytest.raises(OperationError) as caught:
        _run(project_dir, f"invalid/{model}.xml")
    assert caught.value.issue_code is IssueCode.OPERATION_INTENT_INVALID
    assert reason in str(caught.value)
