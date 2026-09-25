from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from datamimic_ce.engine.dsl.api import Dbms
from datamimic_ce.engine.io.client_operations import (
    count_query_length,
    create_mongodb_client,
    create_rdbms_client,
    uses_mysql_sequence_storage,
)
from datamimic_ce.engine.io.clients.client import Client
from datamimic_ce.engine.io.clients.database_client import DatabaseClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig


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
