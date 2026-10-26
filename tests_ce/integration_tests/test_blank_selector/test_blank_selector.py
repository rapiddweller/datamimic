# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""A blank selector on a database source holds no query (#397). It fails with one catalog code before any database
access, and `datamimic run`, `authoring dry-run` and `authoring build` agree on that code. The models are DSL files
next to this test, run on SQLite."""

import sqlite3
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import RejectedBuild, RunRequest
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.errors import IssueCode, UserErrorBase
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
from tests_ce.authoring_project import build_project

_DIR = Path(__file__).resolve().parent
# Every read or count a source makes on an SQL database goes through one of these.
_QUERIES = (
    RdbmsClient.count_query_length,
    RdbmsClient.count_table_length,
    RdbmsClient.get_by_page_with_query,
    RdbmsClient.get_by_page_with_type,
)

# descriptor, element, attribute, product of the model
_BLANK = [
    ("generate_blank.xml", "generate", "selector", "items_read"),
    ("generate_blank_no_count.xml", "generate", "selector", "items_read"),
    ("generate_whitespace.xml", "generate", "selector", "items_read"),
    ("generate_tab_newline.xml", "generate", "selector", "items_read"),
    ("nested_generate_blank.xml", "generate", "selector", "orders"),
    ("variable_blank.xml", "variable", "selector", "rows"),
    ("variable_setup_blank.xml", "variable", "selector", "rows"),
    ("variable_iteration_selector_blank.xml", "variable", "iterationSelector", "rows"),
]
_IDS = [row[0].removesuffix(".xml") for row in _BLANK]


def _record_queries(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    def recorded(method):
        def spy(self, *args, **kwargs):
            calls.append(method.__name__)
            return method(self, *args, **kwargs)

        return spy

    for method in _QUERIES:
        monkeypatch.setattr(RdbmsClient, method.__name__, recorded(method))
    return calls


def _refusal(descriptor: str) -> UserErrorBase:
    engine = DataMimicTest(test_dir=_DIR, filename=descriptor, capture_test_result=True)
    with pytest.raises(UserErrorBase) as caught:
        engine.test_with_timer()
    return caught.value


@pytest.mark.parametrize(("descriptor", "element", "attribute", "product"), _BLANK, ids=_IDS)
def test_run_refuses_the_blank_selector_before_any_database_access(
    monkeypatch, descriptor, element, attribute, product
):
    queries = _record_queries(monkeypatch)
    error = _refusal(descriptor)
    assert error.issue_code is IssueCode.SOURCE_SELECTOR_BLANK
    assert error.location is not None
    assert (error.location.element_tag, error.location.attribute) == (element, attribute)
    assert f"'{attribute}'" in str(error)
    assert "Remove the attribute, or give a query" in str(error)
    assert queries == [], "the refusal must come before the first query"


@pytest.mark.parametrize(("descriptor", "element", "attribute", "product"), _BLANK, ids=_IDS)
def test_dry_run_and_build_report_the_same_code(tmp_path, descriptor, element, attribute, product):
    xml = (_DIR / descriptor).read_text(encoding="utf-8")
    path = PurePosixPath(descriptor)
    dry_run = create_authoring_application(tmp_path, descriptor_path=path).dry_run(
        RunRequest(xml=xml, descriptor_path=path)
    )
    assert [(d.ce_error.issue_code, d.path[-2:]) for d in dry_run.diagnostics if d.ce_error is not None] == [
        (IssueCode.SOURCE_SELECTOR_BLANK, (element, attribute))
    ]

    built = build_project(
        tmp_path,
        xml,
        version="5.0",
        environment_bindings=[{"environment": "db", "family": "database"}],
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": product}, "count": 2}],
    )
    assert isinstance(built, RejectedBuild)
    assert [(d.ce_error.issue_code, d.path[-2:]) for d in built.diagnostics if d.ce_error is not None] == [
        (IssueCode.SOURCE_SELECTOR_BLANK, (element, attribute))
    ]


def test_a_blank_selector_on_a_file_source_is_the_database_only_misuse():
    # It used to raise a bare RuntimeError. Authoring lint refuses this model earlier with DM211.
    assert _refusal("variable_blank_file_source.xml").issue_code is IssueCode.TASK_VARIABLE_SELECTOR_ONLY_DB


def test_a_padded_query_is_not_blank_and_reads_the_rows():
    database = Path.cwd() / "db" / "blank_selector_items.sqlite"
    database.parent.mkdir(exist_ok=True)
    database.unlink(missing_ok=True)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE items (id INTEGER PRIMARY KEY)")
        connection.executemany("INSERT INTO items VALUES (?)", [(1,), (2,)])
    engine = DataMimicTest(test_dir=_DIR, filename="generate_padded_selector.xml", capture_test_result=True)
    engine.test_with_timer()
    assert [row["id"] for row in engine.capture_result()["items_read"]] == [1, 2]
