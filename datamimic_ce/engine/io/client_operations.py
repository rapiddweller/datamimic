"""Operations that runtime tasks may perform without depending on client classes."""

from datamimic_ce.engine.dsl.api import Dbms
from datamimic_ce.engine.io.clients.client import Client
from datamimic_ce.engine.io.clients.database_client import DatabaseClient
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig


def create_rdbms_client(config: RdbmsConnectionConfig, task_id: str) -> Client:
    return RdbmsClient(config, task_id)


def create_mongodb_client(config: MongoDBConnectionConfig) -> Client:
    return MongoDBClient(config)


def count_query_length(client: Client, query: str) -> int | None:
    if not isinstance(client, DatabaseClient):
        return None
    return client.count_query_length(query)


def uses_mysql_sequence_storage(client: Client) -> bool:
    return isinstance(client, RdbmsClient) and client.credential.dbms is Dbms.MYSQL
