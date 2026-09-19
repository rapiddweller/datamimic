# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""A database count-query failure must stay OBSERVABLE in normal runtime logs (ERROR),
never demoted to debug: a broken selector, unavailable DB, or invalid count query that
only logs at debug level is invisible in production. Output-cleanliness for machine-
readable modes is handled at the CLI/MCP boundary (stderr redirection), not by muting
the operational logger globally — a merge review caught exactly that regression once."""

import logging
from unittest.mock import Mock

from sqlalchemy.exc import OperationalError, ProgrammingError

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry
from datamimic_ce.statements.variable_statement import VariableStatement


def _ctx_and_stmt_for_db_source(count_error: Exception) -> tuple[Mock, VariableStatement]:
    client = Mock(spec=RdbmsClient)
    client.count_query_length.side_effect = count_error

    root_ctx = Mock()
    root_ctx.data_source_len = {}
    root_ctx.memstore_manager.contain.return_value = False
    root_ctx.get_client_by_id.return_value = client

    ctx = Mock()
    ctx.root = root_ctx

    stmt = object.__new__(VariableStatement)
    stmt._name = "row"
    stmt._full_name = "row"
    stmt._source = "db"
    stmt._source_entity = None
    stmt._type = None
    stmt._selector = "SELECT count(*) FROM broken"
    stmt._iteration_selector = None
    return ctx, stmt


def test_db_count_query_failure_logs_at_error_level(caplog, monkeypatch) -> None:
    # Other tests run the engine, whose setup_logger() sets propagate=False on the
    # DATAMIMIC logger — force propagation so caplog's root handler sees the record
    # regardless of test execution order (this test passed standalone, failed in-suite).
    monkeypatch.setattr(logging.getLogger("DATAMIMIC"), "propagate", True)
    for exc in (
        ProgrammingError("stmt", {}, Exception("boom")),
        OperationalError("stmt", {}, Exception("db down")),
    ):
        ctx, stmt = _ctx_and_stmt_for_db_source(exc)
        with caplog.at_level(logging.ERROR, logger="DATAMIMIC"):
            caplog.clear()
            DataSourceRegistry.set_data_source_length(ctx, stmt)
        error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert error_records, f"{type(exc).__name__}: count-query failure produced no ERROR log record"
        assert "Cannot get length of database source" in error_records[0].getMessage()
