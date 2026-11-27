# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import traceback
from contextlib import nullcontext
from unittest.mock import MagicMock

import pytest
import sqlalchemy
from sqlalchemy.dialects import mysql

from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.errors import OperationError


@pytest.mark.parametrize(
    ("method", "args", "sequence"),
    [
        ("get_by_page_with_type", ("items",), False),
        ("get_random_rows_by_columns", ("items", ["id"]), False),
        ("update", ("items", [{"id": 1, "value": 2}]), False),
        ("upsert", ("items", [{"id": 1, "value": 2}]), False),
        ("delete", ("items", [{"id": 1}]), False),
        ("get_current_sequence_number", ("secret_sequence",), True),
        ("increase_sequence_number", ("secret_sequence",), True),
        ("reserve_sequence_block", ("secret_sequence", 3), True),
    ],
)
@pytest.mark.parametrize("fixed", [False, True], ids=["negative-control", "normalized"])
def test_sqlalchemy_errors_are_normalized_without_sql(method, args, sequence, fixed, caplog, monkeypatch):
    credential = RdbmsConnectionConfig(
        dbms="postgresql" if sequence else "sqlite",
        host=None,
        port=None,
        user=None,
        password=None,
        database="test",
        db_schema=None,
    )
    client = RdbmsClient(credential)
    engine = sqlalchemy.create_engine("sqlite://")
    client.engine = engine
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE items (id INTEGER PRIMARY KEY, value INTEGER)")

    if not sequence:
        # A real SQLite error after table setup, including a distinctive SQL string.
        @sqlalchemy.event.listens_for(engine, "before_cursor_execute")
        def fail(connection, cursor, statement, parameters, context, executemany):
            sqlalchemy.event.remove(engine, "before_cursor_execute", fail)
            connection.exec_driver_sql("SELECT secret_marker FROM nonexistent_table")

    bound = getattr(client, method)
    if not fixed:
        monkeypatch.setattr(
            "datamimic_ce.engine.io.clients.rdbms_client._normalize_database_errors", lambda target: nullcontext()
        )
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            bound(*args)
        engine.dispose()
        return

    with pytest.raises(OperationError) as caught:
        bound(*args)
    rendered = "".join(traceback.format_exception(caught.value))
    assert "secret_marker" not in rendered
    assert "secret_sequence" not in rendered
    assert "secret_marker" not in caplog.text
    assert isinstance(caught.value.__cause__, sqlalchemy.exc.SQLAlchemyError)
    assert caught.value.__context__ is None
    engine.dispose()


@pytest.mark.parametrize(
    ("failed_statement", "invalidate_fails"),
    [("GET_LOCK", False), ("ALTER TABLE", False), ("RELEASE_LOCK", False), ("ALTER TABLE", True)],
)
def test_mysql_reservation_failure_discards_the_session_without_logging_sql(failed_statement, invalidate_fails, caplog):
    client = RdbmsClient(
        RdbmsConnectionConfig(
            dbms="mysql", host=None, port=None, user=None, password=None, database="test", db_schema=None
        )
    )
    connection = MagicMock(dialect=mysql.dialect())
    counter = iter((1000, 1003))

    def execute(query, params=None):
        sql = str(query)
        if failed_statement in sql:
            raise sqlalchemy.exc.OperationalError("secret_sql", None, RuntimeError("secret_driver_message"))
        result = MagicMock()
        result.scalar.return_value = 1
        if "information_schema.TABLES" in sql:
            result.scalar_one_or_none.return_value = next(counter)
        return result

    connection.execute.side_effect = execute
    if invalidate_fails:
        connection.invalidate.side_effect = sqlalchemy.exc.ProgrammingError(
            "secret_cleanup", None, RuntimeError("secret_cleanup_driver_message")
        )
    engine = MagicMock()
    engine.begin.return_value.__enter__.return_value = connection
    client.engine = engine

    with pytest.raises(OperationError) as caught:
        client.reserve_sequence_block("item_seq", 3, "items", "id")

    connection.invalidate.assert_called_once_with()
    rendered = "".join(traceback.format_exception(caught.value))
    assert "secret_" not in rendered
    assert "secret_" not in caplog.text
    assert isinstance(caught.value.__cause__, sqlalchemy.exc.OperationalError)
    assert caught.value.__context__ is None
