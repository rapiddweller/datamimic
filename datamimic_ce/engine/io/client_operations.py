"""Operations that runtime tasks may perform without depending on client classes."""

from datamimic_ce.engine.dsl.api import Dbms
from datamimic_ce.engine.io.clients.client import Client
from datamimic_ce.engine.io.clients.database_client import DatabaseClient
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.io.contracts import DataSourcePagination


def create_rdbms_client(config: RdbmsConnectionConfig, task_id: str) -> Client:
    return RdbmsClient(config, task_id)


def create_mongodb_client(config: MongoDBConnectionConfig) -> Client:
    return MongoDBClient(config)


def is_database_client(client: Client | None) -> bool:
    return isinstance(client, DatabaseClient)


def is_mongodb_client(client: Client | None) -> bool:
    return isinstance(client, MongoDBClient)


def is_rdbms_client(client: Client | None) -> bool:
    return isinstance(client, RdbmsClient)


def count_query_length(client: Client, query: str) -> int | None:
    if not isinstance(client, DatabaseClient):
        return None
    return client.count_query_length(query)


def database_count_query_length(client: Client, query: str) -> int:
    count = count_query_length(client, query)
    if count is None:
        raise TypeError("Client does not support database query counts")
    return count


def database_get_by_page_with_query(
    client: Client, query: str, pagination: DataSourcePagination | None = None
) -> list:
    if not isinstance(client, DatabaseClient):
        raise TypeError("Client does not support database queries")
    return client.get_by_page_with_query(query, pagination)


def database_get_by_page_with_type(
    client: Client, name: str, pagination: DataSourcePagination | None = None
) -> list:
    if not isinstance(client, DatabaseClient):
        raise TypeError("Client does not support database table or collection reads")
    return client.get_by_page_with_type(name, pagination)


def database_count_table_length(client: Client, name: str) -> int:
    if not isinstance(client, DatabaseClient):
        raise TypeError("Client does not support database table counts")
    return client.count_table_length(name)


def mongodb_count_collection(client: Client, collection: str) -> int:
    if not isinstance(client, MongoDBClient):
        raise TypeError("Client is not a MongoDB client")
    return client.count(collection)


def rdbms_count_query_length(client: Client, query: str, source: str, label: str) -> int | None:
    if not isinstance(client, RdbmsClient):
        raise TypeError("Client is not an RDBMS client")
    from datamimic_ce.engine.io.data_sources.data_source_registry import DataSourceRegistry

    return DataSourceRegistry.rdbms_count_query_length(client, query, source, label)


def database_get_random_rows_by_columns(client: Client | None, name: str, columns: list[str]) -> list[tuple]:
    if not isinstance(client, RdbmsClient | MongoDBClient):
        raise TypeError("Client does not support database column reads")
    return client.get_random_rows_by_columns(name, columns)


def rdbms_get_current_sequence_number(
    client: Client, sequence: str, table: str | None, column: str | None
) -> int:
    if not isinstance(client, RdbmsClient):
        raise TypeError("Client is not an RDBMS client")
    return client.get_current_sequence_number(sequence, table, column)


def rdbms_increase_sequence_number(
    client: Client, sequence: str, increment: int, table: str | None, column: str | None
) -> None:
    if not isinstance(client, RdbmsClient):
        raise TypeError("Client is not an RDBMS client")
    client.increase_sequence_number(sequence, increment, table, column)


def dispose_client_engine(client: Client) -> None:
    if isinstance(client, RdbmsClient) and client.engine is not None:
        client.engine.dispose()
        client.engine = None


def uses_mysql_sequence_storage(client: Client) -> bool:
    return isinstance(client, RdbmsClient) and client.credential.dbms is Dbms.MYSQL
