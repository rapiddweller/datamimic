# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""A delete that reads a database source needs a selector, else it is a clear in disguise (BC-4.0-016).
Generated rows still delete by their own keys. The models are DSL files next to this test, run on SQLite."""

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


def test_a_delete_of_a_whole_database_source_is_refused_and_keeps_the_rows(project_dir):
    database = project_dir / "db" / "delete_sel_whole.sqlite"
    database.parent.mkdir(exist_ok=True)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("CREATE TABLE items (id INTEGER PRIMARY KEY)")
        connection.executemany("INSERT INTO items VALUES (?)", [(1,), (2,)])
    with pytest.raises(OperationError) as caught:
        _run(project_dir, "delete_whole_source.xml")
    assert caught.value.issue_code is IssueCode.OPERATION_INTENT_INVALID
    assert "clientId.clear" in str(caught.value)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM items").fetchone() == (2,)


def test_a_delete_with_a_blank_selector_is_refused_and_keeps_the_rows(project_dir):
    database = project_dir / "db" / "delete_sel_blank.sqlite"
    database.parent.mkdir(exist_ok=True)
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("CREATE TABLE items (id INTEGER PRIMARY KEY)")
        connection.executemany("INSERT INTO items VALUES (?)", [(1,), (2,)])
    with pytest.raises(OperationError) as caught:
        _run(project_dir, "delete_blank_selector.xml")
    assert caught.value.issue_code is IssueCode.OPERATION_INTENT_INVALID
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM items").fetchone() == (2,)


def test_a_delete_with_a_selector_removes_only_the_selected_rows(project_dir):
    assert [row["id"] for row in _run(project_dir, "delete_selected_rows.xml")["items_left"]] == [1]


def test_generated_rows_delete_by_their_own_keys(project_dir):
    assert [row["id"] for row in _run(project_dir, "delete_generated_keys.xml")["items_left"]] == [3]
