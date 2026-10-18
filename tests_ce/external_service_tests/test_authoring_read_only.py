"""Real backend read-only transactions and guarded MongoDB source operations."""

from pathlib import Path
from uuid import uuid4

import pytest
from pymongo import MongoClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.api import load_connection_profile
from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.errors import IssueCode, OperationError


def _profile(directory: str) -> dict[str, str]:
    environment = "local" if get_settings().RUNTIME_ENVIRONMENT == "development" else "environment"
    return load_connection_profile(Path(__file__).parent / directory, environment)


@pytest.mark.parametrize("dbms", [Dbms.POSTGRESQL, Dbms.MYSQL, Dbms.ORACLE])
def test_real_backend_transaction_rejects_writes(dbms: Dbms) -> None:
    profile = _profile("test_rdbms_sql_matrix")
    prefix = dbms.value + ".db."
    config = RdbmsConnectionConfig(
        dbms=dbms,
        host=profile[prefix + "host"],
        port=int(profile[prefix + "port"]),
        database=profile[prefix + "database"],
        user=profile[prefix + "user"],
        password=profile[prefix + "password"],
        db_schema=None,
    )
    writer = RdbmsClient(config)
    reader = RdbmsClient(config.model_copy(update={"read_only": True}))
    table = "ce_ro_" + uuid4().hex[:16]
    created = False
    try:
        writer.execute_sql_script(f"CREATE TABLE {table}(id INTEGER)")
        created = True
        writer.execute_sql_script(f"INSERT INTO {table} VALUES (1)")
        assert reader.get(f"SELECT id FROM {table}") == [(1,)]
        with pytest.raises(OperationError) as rejected:
            reader.get(f"DELETE FROM {table}")
        assert rejected.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED
        with reader.engine.begin() as connection, pytest.raises(DBAPIError):
            connection.execute(text(f"INSERT INTO {table} VALUES (2)"))
        assert writer.get(f"SELECT id FROM {table}") == [(1,)]
    finally:
        if reader.engine is not None:
            reader.engine.dispose()
        if created:
            writer.execute_sql_script(f"DROP TABLE {table}")
        if writer.engine is not None:
            writer.engine.dispose()


def test_real_mongo_reads_keep_collection_unchanged_after_refused_writes() -> None:
    profile = _profile("test_mongodb")
    prefix = "mongodb.mongo."
    config = MongoDBConnectionConfig(
        host=profile[prefix + "host"],
        port=int(profile[prefix + "port"]),
        database=profile[prefix + "database"],
        user=profile[prefix + "user"],
        password=profile[prefix + "password"],
        read_only=True,
    )
    reader = MongoDBClient(config)
    name = "ce_ro_" + uuid4().hex
    with MongoClient(
        host=config.host,
        port=config.port,
        username=config.user,
        password=config.password,
        authSource=profile.get(prefix + "authSource", "admin"),
        serverSelectionTimeoutMS=5000,
    ) as connection:
        collection = connection[config.database][name]
        try:
            collection.insert_one({"id": 1})
            assert reader.get(f'find: "{name}", filter: {{}}')[0]["id"] == 1
            assert reader.get(f'aggregate: "{name}", pipeline: [{{"$match":{{"id":1}}}}]')[0]["id"] == 1
            with pytest.raises(OperationError) as rejected:
                reader.get(f'aggregate: "{name}", pipeline: [{{"$out":"{name}"}}]')
            assert rejected.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED
            with pytest.raises(OperationError):
                reader.delete(name, [{"id": 1}])
            assert list(collection.find({}, {"_id": 0})) == [{"id": 1}]
        finally:
            collection.drop()
