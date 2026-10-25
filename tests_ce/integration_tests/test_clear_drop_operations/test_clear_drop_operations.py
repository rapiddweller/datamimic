# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""target="db.clear" empties a table once and keeps it; clear and drop reject every other shape with I928 (BC-4.0-016).

The models are DSL files next to this test; the RDBMS runs on SQLite. MongoDB drop and clear run in the
external-service tests."""

from pathlib import Path

import pytest

from datamimic_ce.errors import IssueCode, OperationError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> dict:
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_clear_empties_one_table_and_keeps_the_others():
    result = _run("clear_one_table.xml")
    assert result["items_left"] == []
    assert [row["id"] for row in result["kept_left"]] == [1]


def test_cleanup_followed_by_inserts_gives_the_same_rows_on_every_run():
    first = _run("clear_then_insert.xml")["items_left"]
    second = _run("clear_then_insert.xml")["items_left"]
    assert [(row["id"], row["name"]) for row in first] == [(1, "n1"), (2, "n2"), (3, "n3")]
    assert second == first


def test_several_clears_run_in_document_order():
    result = _run("clear_in_dependency_order.xml")
    assert result["parent_left"] == []
    assert result["child_left"] == []


def test_a_clear_reached_through_an_include_runs():
    assert _run("clear_through_include.xml")["items_left"] == []


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
def test_an_invalid_clear_or_drop_fails_with_i928_before_any_database_access(model: str, reason: str):
    with pytest.raises(OperationError) as caught:
        _run(f"invalid/{model}.xml")
    assert caught.value.issue_code is IssueCode.OPERATION_INTENT_INVALID
    assert reason in str(caught.value)
