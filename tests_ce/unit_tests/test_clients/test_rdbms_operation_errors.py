# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import traceback

import pytest
import sqlalchemy

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
    ],
)
@pytest.mark.parametrize("fixed", [False, True], ids=["negative-control", "normalized"])
def test_sqlalchemy_errors_are_normalized_without_sql(method, args, sequence, fixed, caplog):
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
        with pytest.raises(sqlalchemy.exc.SQLAlchemyError):
            bound.__wrapped__(client, *args)
        engine.dispose()
        return

    with pytest.raises(OperationError) as caught:
        bound(*args)
    rendered = "".join(traceback.format_exception(caught.value))
    assert "secret_marker" not in rendered
    assert "secret_sequence" not in rendered
    assert "secret_marker" not in caplog.text
    assert isinstance(caught.value.__cause__, sqlalchemy.exc.SQLAlchemyError)
    engine.dispose()
