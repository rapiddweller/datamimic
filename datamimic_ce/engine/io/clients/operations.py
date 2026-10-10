"""Operations that runtime tasks may perform without depending on client classes."""

import copy
import logging
from typing import TypeGuard

from sqlalchemy.exc import OperationalError, ProgrammingError

from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients.client import Client, RegisteredClient
from datamimic_ce.engine.io.clients.database_client import DatabaseClient
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.io.contracts import DataSourcePagination, SqlScriptClient

logger = logging.getLogger("DATAMIMIC")


def create_rdbms_client(config: RdbmsConnectionConfig, task_id: str) -> Client:
    return RdbmsClient(config, task_id)


def create_mongodb_client(config: MongoDBConnectionConfig) -> Client:
    return MongoDBClient(config)


def clone_client_for_include(client: RegisteredClient) -> RegisteredClient:
    if isinstance(client, RdbmsClient):
        memo = {id(client.engine): None} if client.engine is not None else {}
        return copy.deepcopy(client, memo)
    if isinstance(client, MongoDBClient):
        return copy.deepcopy(client)
    raise TypeError(f"Cannot clone unsupported descriptor client: {type(client).__name__}")


def execute_sql_script(client: SqlScriptClient, query: str) -> None:
    client.execute_sql_script(query)


def is_database_client(client: RegisteredClient | None) -> TypeGuard[DatabaseClient]:
    return isinstance(client, DatabaseClient)


def is_mongodb_client(client: RegisteredClient | None) -> bool:
    return isinstance(client, MongoDBClient)


def is_rdbms_client(client: RegisteredClient | None) -> bool:
    return isinstance(client, RdbmsClient)


def count_query_length(client: RegisteredClient, query: str) -> int | None:
    if not isinstance(client, DatabaseClient):
        return None
    return client.count_query_length(query)


def rdbms_count_source_query(client: RegisteredClient, query: str, source_str: str, query_label: str) -> int | None:
    """Return an RDBMS source count, logging query failures and returning None."""
    if not isinstance(client, RdbmsClient):
        raise TypeError("Client is not an RDBMS client")
    try:
        return client.count_query_length(query=query)
    except (ProgrammingError, OperationalError):
        logger.error(f"Cannot get length of database source '{source_str}' with {query_label} '{query}'")
        return None


def database_count_query_length(client: RegisteredClient, query: str) -> int:
    count = count_query_length(client, query)
    if count is None:
        raise TypeError("Client does not support database query counts")
    return count


def database_get_by_page_with_query(
    client: RegisteredClient, query: str, pagination: DataSourcePagination | None = None
) -> list:
    if not isinstance(client, DatabaseClient):
        raise TypeError("Client does not support database queries")
    return client.get_by_page_with_query(query, pagination)


def database_get_by_page_with_type(
    client: RegisteredClient, name: str, pagination: DataSourcePagination | None = None
) -> list:
    if not isinstance(client, DatabaseClient):
        raise TypeError("Client does not support database table or collection reads")
    return client.get_by_page_with_type(name, pagination)


def database_count_table_length(client: RegisteredClient, name: str) -> int:
    if not isinstance(client, DatabaseClient):
        raise TypeError("Client does not support database table counts")
    return client.count_table_length(name)


def mongodb_count_collection(client: RegisteredClient, collection: str) -> int:
    if not isinstance(client, MongoDBClient):
        raise TypeError("Client is not a MongoDB client")
    return client.count(collection)


def database_get_random_rows_by_columns(client: RegisteredClient | None, name: str, columns: list[str]) -> list[tuple]:
    if not isinstance(client, RdbmsClient | MongoDBClient):
        raise TypeError("Client does not support database column reads")
    return client.get_random_rows_by_columns(name, columns)


def rdbms_get_current_sequence_number(
    client: RegisteredClient, sequence: str, table: str | None, column: str | None
) -> int:
    if not isinstance(client, RdbmsClient):
        raise TypeError("Client is not an RDBMS client")
    return client.get_current_sequence_number(sequence, table, column)


def rdbms_increase_sequence_number(
    client: RegisteredClient, sequence: str, increment: int, table: str | None, column: str | None
) -> None:
    if not isinstance(client, RdbmsClient):
        raise TypeError("Client is not an RDBMS client")
    client.increase_sequence_number(sequence, increment, table, column)


def dispose_client_engine(client: RegisteredClient) -> None:
    if isinstance(client, RdbmsClient) and client.engine is not None:
        client.engine.dispose()
        client.engine = None


def uses_mysql_sequence_storage(client: RegisteredClient) -> bool:
    return isinstance(client, RdbmsClient) and client.credential.dbms is Dbms.MYSQL
