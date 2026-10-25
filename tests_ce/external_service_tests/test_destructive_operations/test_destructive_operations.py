# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""clear and drop against PostgreSQL and MongoDB (BC-4.0-016); the SQLite and validation cases run in
integration_tests/test_clear_drop_operations."""

import logging
from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _run(filename: str, caplog: pytest.LogCaptureFixture) -> tuple[dict, str]:
    logger = logging.getLogger("DATAMIMIC")
    propagate, logger.propagate = logger.propagate, False
    logger.addHandler(caplog.handler)
    try:
        engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
        engine.test_with_timer()
    finally:
        logger.removeHandler(caplog.handler)
        logger.propagate = propagate
    return engine.capture_result(), caplog.text


def test_postgres_cleanup_then_load_gives_the_same_rows_on_every_run(caplog):
    first, log = _run("postgres_clear.xml", caplog)
    second, _ = _run("postgres_clear.xml", caplog)
    assert [(row["id"], row["name"]) for row in first["items_left"]] == [(1, "n1"), (2, "n2"), (3, "n3")]
    assert second["items_left"] == first["items_left"]
    assert "OPERATION | rdbms.clear | table=dm_clear_items | action=clear | backend_action=truncate" in log
    assert "deleted_count=unavailable" in log


def test_postgres_clear_of_a_referenced_table_falls_back_to_delete(caplog):
    result, log = _run("postgres_clear_referenced.xml", caplog)
    assert result["child_left"] == []
    assert result["parent_left"] == []
    assert "OPERATION | rdbms.clear | table=dm_clear_parent | action=clear | backend_action=delete_all" in log


def test_mongo_cleanup_then_load_gives_the_same_documents_on_every_run(caplog):
    first, log = _run("mongo_clear.xml", caplog)
    second, _ = _run("mongo_clear.xml", caplog)
    assert [row["doc_id"] for row in first["docs_left"]] == [1, 2, 3]
    assert [row["doc_id"] for row in second["docs_left"]] == [1, 2, 3]
    assert "OPERATION | mongodb.clear | collection=dm_clear_docs | action=clear" in log


def test_mongo_drop_removes_the_collection(caplog):
    result, log = _run("mongo_drop.xml", caplog)
    assert result["docs_left"] == []
    assert "OPERATION | mongodb.drop | collection=dm_drop_docs | action=drop" in log
