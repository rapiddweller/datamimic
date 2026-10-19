"""Read-only CE clients fail before durable writes or unproved selectors."""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients import sql_dialect
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.errors import IssueCode, OperationError


def sql_client(engine, read_only):
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
    client.engine = engine
    return client


def test_read_only_sqlite_reads_and_blocks_every_mutator_without_writes(tmp_path):
    path = tmp_path / "rows.sqlite"
    writer = create_engine(f"sqlite:///{path}")
    mutable = sql_client(writer, False)
    mutable.execute_sql_script("CREATE TABLE rows(id INTEGER PRIMARY KEY); INSERT INTO rows VALUES (1)")
    reader = sql_client(create_engine(f"sqlite:///{path}"), True)
    assert reader.get("SELECT id FROM rows") == [(1,)]
    attempts = [
        lambda: reader.execute_sql_script("DELETE FROM rows"),
        lambda: reader.insert("rows", [{"id": 2}]),
        lambda: reader.update("rows", [{"id": 1}]),
        lambda: reader.upsert("rows", [{"id": 2}]),
        lambda: reader.delete("rows", [{"id": 1}]),
        lambda: reader.get_current_sequence_number("seq"),
        lambda: reader.increase_sequence_number("seq"),
        lambda: reader.get("DELETE FROM rows RETURNING id"),
    ]
    for attempt in attempts:
        with pytest.raises(OperationError) as error:
            attempt()
        assert error.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED
    assert mutable.get("SELECT id FROM rows") == [(1,)]
    mutable.execute_sql_script("INSERT INTO rows VALUES (2)")
    assert len(mutable.get("SELECT id FROM rows")) == 2


@pytest.mark.parametrize(
    "dbms,query",
    [
        (Dbms.ORACLE, "SELECT seq.nextval FROM dual"),
        (Dbms.MYSQL, 'SELECT 1 /*! INTO OUTFILE "/tmp/output" */'),
        (Dbms.MSSQL, "SELECT * FROM rows WITH (UPDLOCK)"),
        (Dbms.POSTGRESQL, "SELECT id::customtype FROM rows"),
        (Dbms.POSTGRESQL, "SELECT 1; DELETE FROM rows"),
        (Dbms.POSTGRESQL, "WITH erased AS (DELETE FROM rows RETURNING *) SELECT * FROM erased"),
        (Dbms.POSTGRESQL, "SELECT * FROM rows FOR UPDATE"),
        (Dbms.POSTGRESQL, "SELECT nextval('seq')"),
        (Dbms.POSTGRESQL, "SELECT pg_advisory_lock(1)"),
        (Dbms.POSTGRESQL, "SELECT app_side_effect()"),
        (Dbms.MSSQL, "SELECT * INTO copy FROM rows"),
        (Dbms.MYSQL, "SELECT id INTO OUTFILE '/tmp/output' FROM rows"),
        (Dbms.SQLITE, "PRAGMA query_only=OFF"),
        (Dbms.SQLITE, "SELECT load_extension('bad')"),
    ],
)
def test_read_only_selector_ast_rejects_mutation_and_unproved_functions(dbms, query):
    with pytest.raises(OperationError):
        sql_dialect.require_read_only_query(query, dbms)


@pytest.mark.parametrize("dbms", list(Dbms))
def test_read_only_selector_ast_allows_plain_queries_and_safe_aggregates(dbms):
    sql_dialect.require_read_only_query("SELECT id, COUNT(*) FROM rows GROUP BY id", dbms)
    sql_dialect.require_read_only_query("WITH src AS (SELECT id FROM rows) SELECT id FROM src", dbms)


@pytest.mark.parametrize(
    "pipeline",
    [
        [{"$out": "target"}],
        [{"$merge": "target"}],
        [{"$lookup": {"from": "other", "pipeline": [{"$merge": "target"}], "as": "x"}}],
        [{"$facet": {"write": [{"$out": "target"}]}}],
        [{"$project": {"v": {"$function": {"body": "x", "args": [], "lang": "js"}}}}],
    ],
)
def test_read_only_mongo_rejects_parsed_nested_write_pipelines(pipeline):
    client = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=27017, database="test", read_only=True))
    import json

    query = json.dumps({"aggregate": "rows", "pipeline": pipeline})[1:-1]
    with pytest.raises(OperationError) as error:
        client.get(query)
    assert error.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED


def test_sqlite_backend_rejects_direct_write_and_missing_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = RdbmsConnectionConfig(
        dbms=Dbms.SQLITE,
        host=None,
        port=None,
        user=None,
        password=None,
        database="test",
        db_schema=None,
        read_only=True,
    )
    reader = RdbmsClient(config, task_id="test")
    with pytest.raises(OperationError):
        reader.get("SELECT 1")
    assert not (tmp_path / "db").exists()
    (tmp_path / "db").mkdir()
    with create_engine(f"sqlite:///{tmp_path}/db/test.sqlite").begin() as writer:
        writer.execute(text("CREATE TABLE rows(id INTEGER)"))
        writer.execute(text("INSERT INTO rows VALUES(1)"))
    assert reader.get("SELECT id FROM rows") == [(1,)]
    with reader.engine.begin() as connection, pytest.raises(DBAPIError):
        connection.execute(text("INSERT INTO rows VALUES(2)"))
    assert reader.get("SELECT id FROM rows") == [(1,)]


def test_read_only_query_guards_count_and_paging():
    reader = sql_client(create_engine("sqlite://"), True)
    for operation in (reader.count_query_length, reader.get_by_page_with_query):
        with pytest.raises(OperationError):
            operation("DELETE FROM rows RETURNING id")


def test_mssql_read_only_fails_before_connection_creation(monkeypatch):
    config = RdbmsConnectionConfig(
        dbms=Dbms.MSSQL,
        host="localhost",
        port=1433,
        user="u",
        password="p",
        database="test",
        db_schema="dbo",
        read_only=True,
    )
    connect = MagicMock()
    monkeypatch.setattr("datamimic_ce.engine.io.clients.rdbms_client.sqlalchemy.create_engine", connect)
    with pytest.raises(OperationError):
        RdbmsClient(config).get("SELECT 1")
    connect.assert_not_called()


def test_mongo_read_only_reads_and_mutable_writes_use_existing_protocol(monkeypatch):
    collection = MagicMock()
    collection.find.return_value = [{"id": 1}]
    collection.aggregate.return_value = [{"id": 1}]
    collection.count_documents.return_value = 1
    connection = MagicMock()
    connection.__getitem__.return_value.__getitem__.return_value = collection

    @contextmanager
    def connect():
        yield connection

    reader = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=27017, database="test", read_only=True))
    monkeypatch.setattr(reader, "_create_connection", connect)
    assert reader.get('find: "rows", filter: {}') == [{"id": 1}]
    assert reader.count_query_length('find: "rows", filter: {}') == 1
    assert reader.get('aggregate: "rows", pipeline: [{"$match":{"id":1}}]') == [{"id": 1}]
    collection.aggregate.assert_called_once_with([{"$match": {"id": 1}}, {"$sort": {"_id": 1}}])
    for attempt in (
        lambda: reader.insert("rows", [{}], False),
        lambda: reader.update({}, []),
        lambda: reader.upsert({}, []),
        lambda: reader.delete({}, []),
    ):
        with pytest.raises(OperationError):
            attempt()
    collection.insert_many.assert_not_called()
    mutable = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=27017, database="test"))
    monkeypatch.setattr(mutable, "_create_connection", connect)
    mutable.insert("rows", [{"id": 2}], False)
    collection.insert_many.assert_called_once_with([{"id": 2}])


@pytest.mark.parametrize(
    "query",
    [
        'find: "rows", filter: {"$where":"this.id = 2"}',
        'aggregate: "rows", pipeline: [{"$unknown":{}}]',
        'aggregate: "rows", pipeline: [{"$unionWith":{"coll":"other","pipeline":[{"$out":"target"}]}}]',
    ],
)
def test_mongo_unproved_queries_never_open_connection(monkeypatch, query):
    reader = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=27017, database="test", read_only=True))
    connect = MagicMock()
    monkeypatch.setattr(reader, "_create_connection", connect)
    for operation in (reader.get, reader.count_query_length, reader.get_by_page_with_query):
        with pytest.raises(OperationError):
            operation(query)
    connect.assert_not_called()


def test_read_only_sqlite_uri_handles_filename_parameters(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "db").mkdir()
    path = tmp_path / "db" / "source?mode=rw&x.sqlite"
    import sqlite3

    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE rows(id INTEGER)")
    config = RdbmsConnectionConfig(
        dbms=Dbms.SQLITE,
        host=None,
        port=None,
        user=None,
        password=None,
        database="source?mode=rw&x",
        db_schema=None,
        read_only=True,
        isolation_level="AUTOCOMMIT",
        execution_options={"isolation_level": "AUTOCOMMIT"},
    )
    reader = RdbmsClient(config, task_id="test")
    assert reader.get("SELECT id FROM rows") == []
    with reader.engine.begin() as connection, pytest.raises(DBAPIError):
        connection.execute(text("INSERT INTO rows VALUES(1)"))
    assert reader._engine_kwargs["isolation_level"] == "SERIALIZABLE"
    assert "execution_options" not in reader._engine_kwargs
