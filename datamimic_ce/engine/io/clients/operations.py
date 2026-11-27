"""Operations that runtime tasks may perform without depending on client classes."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, TypeGuard

from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients.client import Client, RegisteredClient
from datamimic_ce.engine.io.clients.database_client import DatabaseClient
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.io.contracts import ColumnKind, DataSourcePagination, SqlScriptClient
from datamimic_ce.errors import IssueCode, OperationError

if TYPE_CHECKING:
    from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient

logger = logging.getLogger("DATAMIMIC")


def create_rdbms_client(config: RdbmsConnectionConfig, task_id: str) -> Client:
    from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient

    return RdbmsClient(config, task_id)


def create_mongodb_client(config: MongoDBConnectionConfig) -> Client:
    return MongoDBClient(config)


def clone_client_for_include(client: RegisteredClient) -> RegisteredClient:
    if is_rdbms_client(client):
        memo = {id(client.engine): None} if client.engine is not None else {}
        return copy.deepcopy(client, memo)
    if isinstance(client, MongoDBClient):
        return copy.deepcopy(client)
    raise TypeError(f"Cannot clone unsupported descriptor client: {type(client).__name__}")


def execute_sql_script(client: SqlScriptClient, query: str) -> None:
    client.execute_sql_script(query)


def is_database_client(client: RegisteredClient | None) -> TypeGuard[DatabaseClient]:
    return isinstance(client, DatabaseClient)


def is_mongodb_client(client: RegisteredClient | None) -> TypeGuard[MongoDBClient]:
    return isinstance(client, MongoDBClient)


def is_rdbms_client(client: RegisteredClient | None) -> TypeGuard[RdbmsClient]:
    if not isinstance(client, DatabaseClient) or is_mongodb_client(client):
        return False
    from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient

    return isinstance(client, RdbmsClient)


def rdbms_client_dbms(client: RegisteredClient | None) -> Dbms | None:
    return client.dbms if is_rdbms_client(client) else None


def planned_create_table_ddl(
    dbms: Dbms,
    entity: str,
    columns: tuple[tuple[str, ColumnKind], ...],
    primary_key: tuple[str, ...],
    schema: str | None,
) -> str:
    """The CREATE TABLE statement that a run would execute, for Build, which creates nothing."""
    from datamimic_ce.engine.io.clients.rdbms_client import create_table_ddl, create_table_definition

    return create_table_ddl(create_table_definition(entity, columns, primary_key, schema), dbms)


def count_query_length(client: RegisteredClient, query: str) -> int | None:
    if not isinstance(client, DatabaseClient):
        return None
    return client.count_query_length(query)


def rdbms_count_source_query(client: RegisteredClient, query: str, source_str: str, query_label: str) -> int | None:
    """Return an RDBMS source count, logging query failures and returning None."""
    if not is_rdbms_client(client):
        raise TypeError("Client is not an RDBMS client")
    from sqlalchemy.exc import OperationalError, ProgrammingError

    try:
        return client.count_query_length(query=query)
    except (ProgrammingError, OperationalError, OperationError) as error:
        if isinstance(error, OperationError) and not (
            error.issue_code is IssueCode.OPERATION_EXECUTION_FAILED
            and isinstance(error.__cause__, ProgrammingError | OperationalError)
        ):
            raise
        logger.error(f"Cannot get length of database source '{source_str}' with {query_label}")
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
    if is_rdbms_client(client) or is_mongodb_client(client):
        return client.get_random_rows_by_columns(name, columns)
    raise TypeError("Client does not support database column reads")


def rdbms_get_current_sequence_number(
    client: RegisteredClient, sequence: str, table: str | None, column: str | None
) -> int:
    if not is_rdbms_client(client):
        raise TypeError("Client is not an RDBMS client")
    return client.get_current_sequence_number(sequence, table, column)


def rdbms_increase_sequence_number(
    client: RegisteredClient, sequence: str, increment: int, table: str | None, column: str | None
) -> None:
    if not is_rdbms_client(client):
        raise TypeError("Client is not an RDBMS client")
    client.increase_sequence_number(sequence, increment, table, column)


def rdbms_reserve_sequence_block(
    client: Client, sequence: str, count: int, table: str | None, column: str | None
) -> int:
    if not is_rdbms_client(client):
        raise TypeError("Client is not an RDBMS client")
    return client.reserve_sequence_block(sequence, count, table, column)


def dispose_client_engine(client: RegisteredClient) -> None:
    if is_rdbms_client(client) and client.engine is not None:
        client.engine.dispose()
        client.engine = None


def uses_mysql_sequence_storage(client: RegisteredClient) -> bool:
    return is_rdbms_client(client) and client.credential.dbms is Dbms.MYSQL
