# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The value of a database selector must reach no log line at INFO or above."""

import logging
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import OperationalError

from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients.operations import rdbms_count_source_query
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.clients.sql_dialect import _parse_selector

TOKEN = "zq7_secret_token"


@pytest.fixture(autouse=True)
def _propagate(monkeypatch):
    monkeypatch.setattr(logging.getLogger("DATAMIMIC"), "propagate", True)


def _assert_token_absent(caplog) -> None:
    lines = [record.getMessage() for record in caplog.records if record.levelno >= logging.INFO]
    assert lines, "the scenario must log something, or the test proves nothing"
    assert not [line for line in lines if TOKEN in line]


@pytest.mark.parametrize("label", ["selector", "iterationSelector"])
def test_count_failure_log_has_no_selector_value(caplog, label) -> None:
    client = Mock(spec=RdbmsClient)
    client.count_query_length.side_effect = OperationalError("stmt", {}, Exception("db down"))
    with caplog.at_level(logging.INFO, logger="DATAMIMIC"):
        assert rdbms_count_source_query(client, f"SELECT '{TOKEN}' FROM missing", "db", label) is None
    _assert_token_absent(caplog)


def test_unparseable_selector_log_has_no_selector_value(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="DATAMIMIC"):
        _parse_selector(f"SELECT '{TOKEN}' FROM (((", Dbms.POSTGRESQL)
    _assert_token_absent(caplog)


def test_unpaged_query_read_log_has_no_selector_value(caplog) -> None:
    client = Mock(spec=RdbmsClient)
    client.get.return_value = []
    client._require_read_query = Mock()
    with caplog.at_level(logging.INFO, logger="DATAMIMIC"):
        RdbmsClient.get_by_page_with_query(client, f"SELECT '{TOKEN}' FROM items", None)
    _assert_token_absent(caplog)
