from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from datamimic_ce.engine.dsl.api import Dbms
from datamimic_ce.engine.io.client_operations import (
    count_query_length,
    create_mongodb_client,
    create_rdbms_client,
    database_get_by_page_with_query,
    database_get_random_rows_by_columns,
    is_database_client,
    is_mongodb_client,
    is_rdbms_client,
    mongodb_count_collection,
    rdbms_get_current_sequence_number,
    uses_mysql_sequence_storage,
)
from datamimic_ce.engine.io.clients.client import Client
from datamimic_ce.engine.io.clients.database_client import DatabaseClient
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.io.contracts import DataSourcePagination


def test_create_rdbms_client_delegates_config_and_task_id() -> None:
    config = MagicMock(spec=RdbmsConnectionConfig)
    client = object()
    with patch("datamimic_ce.engine.io.client_operations.RdbmsClient", return_value=client) as factory:
        assert create_rdbms_client(config, "task-1") is client
    factory.assert_called_once_with(config, "task-1")


def test_create_mongodb_client_delegates_config() -> None:
    config = MagicMock(spec=MongoDBConnectionConfig)
    client = object()
    with patch("datamimic_ce.engine.io.client_operations.MongoDBClient", return_value=client) as factory:
        assert create_mongodb_client(config) is client
    factory.assert_called_once_with(config)


def test_count_query_length_only_calls_database_clients() -> None:
    database = MagicMock(spec=DatabaseClient)
    database.count_query_length.return_value = 12
    assert count_query_length(database, "select 1") == 12
    database.count_query_length.assert_called_once_with("select 1")

    other = MagicMock(spec=Client)
    assert count_query_length(other, "select 1") is None


def test_mysql_sequence_storage_is_specific_to_mysql_rdbms() -> None:
    mysql = object.__new__(RdbmsClient)
    mysql._credential = SimpleNamespace(dbms=Dbms.MYSQL)
    postgres = object.__new__(RdbmsClient)
    postgres._credential = SimpleNamespace(dbms=Dbms.POSTGRESQL)

    assert uses_mysql_sequence_storage(mysql)
    assert not uses_mysql_sequence_storage(postgres)
    assert not uses_mysql_sequence_storage(MagicMock(spec=Client))


def test_client_operations_reject_unsupported_client_kinds() -> None:
    other = MagicMock(spec=Client)
    rdbms = MagicMock(spec=RdbmsClient)
    mongodb = MagicMock(spec=MongoDBClient)

    assert not any((is_database_client(other), is_mongodb_client(other), is_rdbms_client(other)))
    with pytest.raises(TypeError, match="database queries"):
        database_get_by_page_with_query(other, "select 1")
    with pytest.raises(TypeError, match="database column reads"):
        database_get_random_rows_by_columns(other, "table", ["id"])
    with pytest.raises(TypeError, match="not a MongoDB"):
        mongodb_count_collection(rdbms, "collection")
    with pytest.raises(TypeError, match="not an RDBMS"):
        rdbms_get_current_sequence_number(mongodb, "seq", None, None)


def test_database_query_operation_forwards_pagination() -> None:
    rdbms = MagicMock(spec=RdbmsClient)
    pagination = DataSourcePagination(skip=0, limit=1)
    rows = [{"id": 1}]
    rdbms.get_by_page_with_query.return_value = rows

    assert database_get_by_page_with_query(rdbms, "select 1", pagination) is rows
    rdbms.get_by_page_with_query.assert_called_once_with("select 1", pagination)
