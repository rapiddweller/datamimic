"""Real backend read-only transactions and guarded MongoDB source operations."""

from pathlib import Path
from uuid import uuid4

import oracledb
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
        # Oracle READ ONLY snapshots can reject newly created tables with ORA-01466.
        read_query = "SELECT 1 FROM DUAL" if dbms is Dbms.ORACLE else f"SELECT id FROM {table}"
        assert reader.get(read_query) == [(1,)]
        with pytest.raises(OperationError) as rejected:
            reader.get(f"DELETE FROM {table}")
        assert rejected.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED
        with reader.engine.begin() as connection, pytest.raises(DBAPIError) as native_rejected:
            connection.execute(text(f"INSERT INTO {table} VALUES (2)"))
        if dbms is Dbms.ORACLE:
            assert isinstance(native_rejected.value.orig, oracledb.DatabaseError)
            assert native_rejected.value.orig.args[0].code == 1456
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


def test_real_mongo_object_ids_survive_bounded_capture(tmp_path) -> None:
    from bson import ObjectId

    from datamimic_ce.authoring import create_authoring_application
    from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
    from datamimic_ce.authoring.domain.capture import CapturedObjectId
    from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest, RunRequest
    from datamimic_ce.engine.runtime.api import create_run_session
    from datamimic_ce.engine.runtime.contracts import RunRequest as RuntimeRequest

    profile = _profile("test_mongodb")
    prefix = "mongodb.mongo."
    name = "ce_capture_" + uuid4().hex
    identifiers = [ObjectId(), ObjectId()]
    native_rows = [{"_id": identifier, "nested": {"ids": [identifier]}} for identifier in identifiers]
    expected = tuple({"_id": str(identifier), "nested": {"ids": [str(identifier)]}} for identifier in identifiers)
    conf = tmp_path / "conf"
    conf.mkdir()
    for environment in ("local", "environment"):
        (conf / f"{environment}.env.properties").write_text(
            "\n".join(f"{key}={value}" for key, value in profile.items()), encoding="utf-8"
        )
    xml = f"""<setup rngSeed="7"><mongodb id="mongodb"/>
      <generate name="rows" source="mongodb" distribution="ordered"
        selector="aggregate: '{name}', pipeline: [{{'$sort': {{'_id': 1}}}}]"/>
    </setup>"""
    descriptor = tmp_path / "model.xml"
    descriptor.write_text(xml, encoding="utf-8")
    with MongoClient(
        host=profile[prefix + "host"],
        port=int(profile[prefix + "port"]),
        username=profile[prefix + "user"],
        password=profile[prefix + "password"],
        authSource=profile.get(prefix + "authSource", "admin"),
        serverSelectionTimeoutMS=5000,
    ) as connection:
        collection = connection[profile[prefix + "database"]][name]
        try:
            collection.insert_many(native_rows)
            session = create_run_session(
                RuntimeRequest(
                    descriptor_path=descriptor,
                    test_mode=True,
                    profile_loader=lambda *_: profile,
                )
            )
            session.execute()
            raw = session.capture_test_result()["rows"]
            assert raw == native_rows
            assert all(isinstance(row["_id"], ObjectId) for row in raw)
            complete = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(BoundedExecutionRequest(xml=xml))
            assert complete.ok, complete.diagnostics
            product = complete.captured.get("rows")
            assert product.capture.complete
            assert product.rows == tuple(
                {
                    "_id": CapturedObjectId(value=str(identifier)),
                    "nested": {"ids": [CapturedObjectId(value=str(identifier))]},
                }
                for identifier in identifiers
            )
            result = create_authoring_application(workspace_root=tmp_path).dry_run(RunRequest(xml=xml, sample_rows=1))
            assert result.ok, result.diagnostics
            assert result.products[0].count == 2
            assert result.products[0].rows == expected[:1]
            assert list(collection.find().sort("_id", 1)) == native_rows
        finally:
            collection.drop()
