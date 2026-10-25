# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The client side of clear and drop (BC-4.0-016): the SQL and MongoDB operations, the per-client operation sets and
the count gate. Model-level behavior is pinned by integration_tests/test_clear_drop_operations."""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.dsl.vocabulary.enums.operation_enums import ExportOperation, split_targets
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.io.exporters.registry import create_exporter_list
from datamimic_ce.errors import IssueCode, OperationError


def _sql_client(path, read_only=False) -> RdbmsClient:
    client = RdbmsClient(
        RdbmsConnectionConfig(
            dbms=Dbms.SQLITE,
            host=None,
            port=None,
            user=None,
            password=None,
            database="test",
            db_schema=None,
            read_only=read_only,
        )
    )
    client.engine = create_engine(f"sqlite:///{path}")
    return client


def test_sql_clear_removes_every_row_and_keeps_the_table(tmp_path, caplog):
    client = _sql_client(tmp_path / "t.db")
    client.execute_sql_script(
        "CREATE TABLE Rows(id INTEGER PRIMARY KEY); INSERT INTO Rows VALUES (1); INSERT INTO Rows VALUES (2)"
    )
    with caplog.at_level("INFO", logger="DATAMIMIC"):
        client.clear("rows")  # the table name matches case-insensitively, as for delete
    assert client.get("SELECT id FROM Rows") == []
    client.execute_sql_script("INSERT INTO Rows VALUES (3)")  # the table is still there
    assert (
        "OPERATION | rdbms.clear | table=Rows | action=clear | backend_action=delete_all | deleted_count=2"
        in caplog.text
    )


def test_sql_clear_on_a_missing_table_is_a_catalog_error(tmp_path):
    with pytest.raises(OperationError) as caught:
        _sql_client(tmp_path / "t.db").clear("missing")
    assert caught.value.issue_code is IssueCode.OPERATION_EXECUTION_FAILED


def test_sql_clear_is_blocked_on_a_read_only_connection(tmp_path):
    with pytest.raises(OperationError) as caught:
        _sql_client(tmp_path / "t.db", read_only=True).clear("rows")
    assert caught.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED


class _Engine:
    """A stand-in engine: records the statements and can refuse TRUNCATE."""

    def __init__(self, dialect: str, refuse_truncate: bool = False) -> None:
        self.dialect = MagicMock()
        self.dialect.name = dialect
        self.dialect.identifier_preparer.format_table.return_value = '"s"."t"'
        self.statements: list[str] = []
        self._refuse_truncate = refuse_truncate

    @contextmanager
    def begin(self):
        connection = MagicMock()

        def execute(statement):
            self.statements.append(str(statement))
            if self._refuse_truncate and "TRUNCATE" in str(statement):
                raise OperationalError("TRUNCATE", {}, Exception("referenced by a foreign key"))
            result = MagicMock()
            result.rowcount = 4
            return result

        connection.execute = execute
        yield connection


@pytest.mark.parametrize(
    ("dialect", "action", "deleted", "first_statement"),
    [
        ("postgresql", "truncate", None, 'TRUNCATE TABLE "s"."t"'),
        ("mssql", "truncate", None, 'TRUNCATE TABLE "s"."t"'),
        ("oracle", "delete_all", 4, "DELETE FROM t"),
        ("mysql", "delete_all", 4, "DELETE FROM t"),
    ],
)
def test_clear_uses_truncate_on_postgresql_and_mssql_and_delete_elsewhere(dialect, action, deleted, first_statement):
    from sqlalchemy import Column, Integer, MetaData, Table

    table = Table("t", MetaData(), Column("id", Integer, primary_key=True))
    engine = _Engine(dialect)
    assert RdbmsClient._truncate_or_delete_all(engine, table) == (action, deleted)
    assert engine.statements[0] == first_statement


def test_a_refused_truncate_falls_back_to_a_full_delete_with_a_row_count():
    from sqlalchemy import Column, Integer, MetaData, Table

    table = Table("t", MetaData(), Column("id", Integer, primary_key=True))
    engine = _Engine("postgresql", refuse_truncate=True)
    assert RdbmsClient._truncate_or_delete_all(engine, table) == ("delete_all", 4)
    assert [statement.split()[0] for statement in engine.statements] == ["TRUNCATE", "DELETE"]


def _mongo(monkeypatch, read_only=False):
    collection = MagicMock()
    collection.delete_many.return_value.deleted_count = 5
    connection = {"test": {"orders": collection}}

    @contextmanager
    def connect():
        yield connection

    client = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=27017, database="test", read_only=read_only))
    monkeypatch.setattr(client, "_create_connection", connect)
    return client, collection


def test_mongo_clear_deletes_all_documents_and_keeps_the_collection(monkeypatch, caplog):
    client, collection = _mongo(monkeypatch)
    with caplog.at_level("INFO", logger="DATAMIMIC"):
        client.clear("orders")
    collection.delete_many.assert_called_once_with({})
    collection.drop.assert_not_called()
    assert "OPERATION | mongodb.clear | collection=orders | action=clear | deleted_count=5" in caplog.text


def test_mongo_drop_removes_the_collection(monkeypatch, caplog):
    client, collection = _mongo(monkeypatch)
    with caplog.at_level("INFO", logger="DATAMIMIC"):
        client.drop("orders")
    collection.drop.assert_called_once_with()
    collection.delete_many.assert_not_called()
    assert "OPERATION | mongodb.drop | collection=orders | action=drop" in caplog.text


def test_mongo_clear_and_drop_are_blocked_on_a_read_only_connection(monkeypatch):
    client, collection = _mongo(monkeypatch, read_only=True)
    for attempt in (lambda: client.clear("orders"), lambda: client.drop("orders")):
        with pytest.raises(OperationError) as caught:
            attempt()
        assert caught.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED
    collection.delete_many.assert_not_called()
    collection.drop.assert_not_called()


def test_mongo_clear_rejects_a_blank_collection(monkeypatch):
    client, _ = _mongo(monkeypatch)
    with pytest.raises(ValueError, match="collection name"):
        client.clear("  ")


def test_the_target_suffix_names_a_typed_operation():
    assert ExportOperation.from_target("db.clear") == ("db", ExportOperation.CLEAR)
    assert ExportOperation.from_target("mongo.drop") == ("mongo", ExportOperation.DROP)
    assert ExportOperation.from_target("db.deleted") is None
    assert ExportOperation.from_target("CSV") is None
    assert split_targets("db.clear, CSV(separator=',')") == ["db.clear", "CSV(separator=',')"]


def _context_with(client):
    context = MagicMock()
    context.get_client_by_id.return_value = client
    return context


def test_the_operation_set_depends_on_the_client_family(tmp_path):
    sql = _context_with(_sql_client(tmp_path / "t.db"))
    with pytest.raises(OperationError) as drop:
        create_exporter_list(sql, "rows", None, ["db.drop"])
    assert drop.value.issue_code is IssueCode.OPERATION_INTENT_INVALID
    assert "drop is supported only for MongoDB collections" in str(drop.value)
    with pytest.raises(ValueError, match=r"Allowed operations: update, upsert, delete, clear\."):
        create_exporter_list(sql, "rows", None, ["db.patch"])
    mongo = _context_with(MongoDBClient(MongoDBConnectionConfig(host="localhost", port=27017, database="test")))
    with pytest.raises(ValueError, match=r"Allowed operations: update, upsert, delete, clear, drop\."):
        create_exporter_list(mongo, "rows", None, ["mongo.patch"])
    with_operation, without_operation = create_exporter_list(mongo, "rows", None, ["mongo.drop"])
    assert [operation for _, operation in with_operation] == [ExportOperation.DROP]
    assert without_operation == []


def test_clear_and_drop_need_no_count_but_delete_still_does():
    assert GenerateModel(name="c", target="db.clear", targetEntity="t")
    assert GenerateModel(name="c", target="mongo.drop", targetEntity="t")
    with pytest.raises(ValidationError, match="Missing attribute 'count'"):
        GenerateModel(name="c", target="db.delete")
    with pytest.raises(ValidationError, match="Missing attribute 'count'"):
        GenerateModel(name="c", target="db.deleted")
