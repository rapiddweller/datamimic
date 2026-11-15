# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The value of a database selector must reach no log line at any level, nor to the cause chain of a raised error."""

import logging
import traceback
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.exc import OperationalError

from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients.operations import rdbms_count_source_query
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.clients.sql_dialect import _parse_selector
from datamimic_ce.errors import IssueCode, OperationError

TOKEN = "zq7_secret_token"


@pytest.fixture(autouse=True)
def _propagate(monkeypatch):
    monkeypatch.setattr(logging.getLogger("DATAMIMIC"), "propagate", True)


def _assert_token_absent(caplog) -> None:
    lines = [record.getMessage() for record in caplog.records]
    assert lines, "the scenario must log something, or the test proves nothing"
    assert not [line for line in lines if TOKEN in line]


@pytest.mark.parametrize("label", ["selector", "iterationSelector"])
def test_count_failure_log_has_no_selector_value(caplog, label) -> None:
    client = Mock(spec=RdbmsClient)
    client.count_query_length.side_effect = OperationalError("stmt", {}, Exception("db down"))
    with caplog.at_level(logging.DEBUG, logger="DATAMIMIC"):
        assert rdbms_count_source_query(client, f"SELECT '{TOKEN}' FROM missing", "db", label) is None
    _assert_token_absent(caplog)


def test_unparseable_selector_log_has_no_selector_value(caplog) -> None:
    with caplog.at_level(logging.DEBUG, logger="DATAMIMIC"):
        _parse_selector(f"SELECT '{TOKEN}' FROM (((", Dbms.POSTGRESQL)
    _assert_token_absent(caplog)


def test_unpaged_query_read_log_has_no_selector_value(caplog) -> None:
    client = Mock(spec=RdbmsClient)
    client.get.return_value = []
    client._require_read_query = Mock()
    with caplog.at_level(logging.DEBUG, logger="DATAMIMIC"):
        RdbmsClient.get_by_page_with_query(client, f"SELECT '{TOKEN}' FROM items", None)
    _assert_token_absent(caplog)


def _chain_text(error: BaseException) -> str:
    return "".join(traceback.format_exception(error))


def _failing_engine():
    connection = MagicMock()
    connection.execute.side_effect = OperationalError(f"SELECT '{TOKEN}' FROM items", {}, Exception("db down"))
    connection.exec_driver_sql.side_effect = connection.execute.side_effect
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    return engine


@pytest.mark.parametrize("call", ["get", "execute_sql_script"])
def test_database_operation_error_chain_has_no_selector_value(call) -> None:
    client = Mock(spec=RdbmsClient)
    client._require_read_query = Mock()
    client._require_write = Mock()
    client._create_engine.return_value = _failing_engine()
    client._credential = Mock(dbms=Dbms.POSTGRESQL)
    with (
        patch(
            "datamimic_ce.engine.io.clients.rdbms_client.sql_dialect.split_script", return_value=[f"SELECT '{TOKEN}'"]
        ),
        pytest.raises(OperationError) as caught,
    ):
        getattr(RdbmsClient, call)(client, f"SELECT '{TOKEN}' FROM items")
    assert caught.value.issue_code == IssueCode.OPERATION_EXECUTION_FAILED
    assert "OperationalError" in str(caught.value)
    assert isinstance(caught.value.__cause__, OperationalError)
    assert caught.value.__cause__.statement is None
    assert TOKEN not in _chain_text(caught.value)
    assert TOKEN not in repr(caught.value.__cause__)
    assert TOKEN not in str(caught.value)
