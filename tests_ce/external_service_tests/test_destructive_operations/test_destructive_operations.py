# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""clear and drop against PostgreSQL and MongoDB (BC-4.0-016). The cases follow the EE external tests for the
same contract; the SQLite and validation cases run in integration_tests/test_clear_drop_operations."""

import logging
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from datamimic_ce.engine.dsl.api import parse_properties
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.errors import IssueCode, OperationError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _properties() -> dict[str, str]:
    name = (
        "local.env.properties" if get_settings().RUNTIME_ENVIRONMENT == "development" else "environment.env.properties"
    )
    return parse_properties(_DIR / "conf" / name)


def _run(filename: str, caplog: pytest.LogCaptureFixture) -> tuple[dict, str]:
    logger = logging.getLogger("DATAMIMIC")
    propagate, logger.propagate = logger.propagate, False
    logger.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger="DATAMIMIC")  # the run keeps an existing stream handler and its level
    try:
        engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
        engine.test_with_timer()
    finally:
        logger.removeHandler(caplog.handler)
        logger.propagate = propagate
    return engine.capture_result(), caplog.text


@pytest.fixture
def pg() -> Iterator[Engine]:
    props = _properties()
    url = (
        f"postgresql+psycopg2://{props['postgresql.db.user']}:{quote_plus(props['postgresql.db.password'])}"
        f"@{props['postgresql.db.host']}:{props['postgresql.db.port']}/{props['postgresql.db.database']}"
    )
    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def mongo_db():
    props = _properties()
    client = MongoClient(
        host=props["mongodb.mongo.host"],
        port=int(props["mongodb.mongo.port"]),
        username=props["mongodb.mongo.user"],
        password=props["mongodb.mongo.password"],
        authSource=props.get("mongodb.mongo.authSource", "admin"),
    )
    yield client[props["mongodb.mongo.database"]]
    client.close()


def _scalar(engine: Engine, sql: str) -> object:
    with engine.connect() as connection:
        return connection.execute(text(sql)).scalar_one()


def _catalog(engine: Engine, table: str) -> dict[str, list]:
    """Indexes and constraints of a table, as PostgreSQL reports them."""
    with engine.connect() as connection:
        indexes = connection.execute(
            text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = :t ORDER BY indexname"), {"t": table}
        ).all()
        constraints = connection.execute(
            text(
                "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid = CAST(:t AS regclass) ORDER BY conname"
            ),
            {"t": table},
        ).all()
    return {"indexes": [tuple(row) for row in indexes], "constraints": [tuple(row) for row in constraints]}


# ---- PostgreSQL ----


def test_postgres_cleanup_then_load_gives_the_same_rows_on_every_run(caplog):
    first, log = _run("postgres_clear.xml", caplog)
    second, _ = _run("postgres_clear.xml", caplog)
    assert [(row["id"], row["name"]) for row in first["items_left"]] == [(1, "n1"), (2, "n2"), (3, "n3")]
    assert second["items_left"] == first["items_left"]
    assert "OPERATION | rdbms.clear | table=dm_clear_items | action=clear | backend_action=truncate" in log
    assert "deleted_count=unavailable" in log


def test_postgres_clear_removes_seeded_rows_and_keeps_the_table_indexes_and_constraints(pg, caplog):
    _run("postgres_seed_and_clear.xml", caplog)
    assert _scalar(pg, "SELECT COUNT(*) FROM dm_clear_seeded") == 0
    catalog = _catalog(pg, "dm_clear_seeded")
    assert [name for name, _ in catalog["indexes"]] == ["dm_clear_seeded_pkey", "dm_clear_seeded_status_idx"]
    assert [name for name, _ in catalog["constraints"]] == ["dm_clear_seeded_pkey"]
    with pg.begin() as connection:
        connection.execute(text("INSERT INTO dm_clear_seeded VALUES (1, 'again')"))  # the table is still usable
    assert _scalar(pg, "SELECT COUNT(*) FROM dm_clear_seeded") == 1


def test_postgres_clear_of_a_referenced_table_falls_back_to_delete_and_keeps_the_constraint(pg, caplog):
    result, log = _run("postgres_clear_referenced.xml", caplog)
    assert result["child_left"] == []
    assert result["parent_left"] == []
    assert "OPERATION | rdbms.clear | table=dm_clear_parent | action=clear | backend_action=delete_all" in log
    assert any("FOREIGN KEY" in definition for _, definition in _catalog(pg, "dm_clear_child")["constraints"])


def test_postgres_clear_of_an_empty_table_is_not_an_error(pg, caplog):
    _, log = _run("postgres_clear_empty.xml", caplog)
    assert _scalar(pg, "SELECT COUNT(*) FROM dm_clear_empty") == 0
    assert "OPERATION | rdbms.clear | table=dm_clear_empty | action=clear" in log


def test_postgres_clear_on_a_read_only_client_is_a_user_error_and_changes_nothing(pg, caplog):
    with pytest.raises(OperationError) as caught:
        _run("postgres_clear_read_only.xml", caplog)
    assert caught.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED
    assert _scalar(pg, "SELECT COUNT(*) FROM dm_clear_guarded") == 1


def test_postgres_clear_with_a_source_is_refused_before_the_table_is_touched(pg, caplog):
    with pytest.raises(OperationError) as caught:
        _run("postgres_clear_invalid.xml", caplog)
    assert caught.value.issue_code is IssueCode.OPERATION_INTENT_INVALID
    assert _scalar(pg, "SELECT COUNT(*) FROM dm_clear_untouched") == 2


# ---- MongoDB ----


def test_mongo_cleanup_then_load_gives_the_same_documents_on_every_run(caplog):
    first, log = _run("mongo_clear.xml", caplog)
    second, _ = _run("mongo_clear.xml", caplog)
    assert [row["doc_id"] for row in first["docs_left"]] == [1, 2, 3]
    assert [row["doc_id"] for row in second["docs_left"]] == [1, 2, 3]
    assert "OPERATION | mongodb.clear | collection=dm_clear_docs | action=clear" in log


def test_mongo_clear_keeps_the_collection_its_indexes_validator_and_options(mongo_db, caplog):
    name = "dm_clear_preserve"
    mongo_db[name].drop()
    mongo_db.create_collection(
        name, validator={"$jsonSchema": {"bsonType": "object", "required": ["kind"]}}, validationLevel="strict"
    )
    mongo_db[name].create_index("kind", name="kind_idx")
    mongo_db[name].insert_many([{"_id": 1, "kind": "keep"}, {"_id": 2, "kind": "remove"}])

    def options() -> dict:
        return mongo_db.command("listCollections", filter={"name": name})["cursor"]["firstBatch"][0]["options"]

    before_indexes, before_options = list(mongo_db[name].list_indexes()), options()
    try:
        _, log = _run("mongo_clear_preserve.xml", caplog)
        assert name in mongo_db.list_collection_names()
        assert mongo_db[name].count_documents({}) == 0
        assert list(mongo_db[name].list_indexes()) == before_indexes
        assert options() == before_options
        assert f"OPERATION | mongodb.clear | collection={name} | action=clear | deleted_count=2" in log
        assert "action=drop" not in log
    finally:
        mongo_db[name].drop()


def test_mongo_drop_removes_the_whole_collection(mongo_db, caplog):
    name = "dm_drop_whole"
    mongo_db[name].drop()
    mongo_db[name].insert_one({"_id": 1})
    mongo_db[name].create_index("kind", name="kind_idx")
    try:
        _, log = _run("mongo_drop_preserve.xml", caplog)
        assert name not in mongo_db.list_collection_names()
        assert f"OPERATION | mongodb.drop | collection={name} | action=drop" in log
    finally:
        mongo_db[name].drop()


def test_mongo_drop_after_load_leaves_no_documents(caplog):
    result, log = _run("mongo_drop.xml", caplog)
    assert result["docs_left"] == []
    assert "OPERATION | mongodb.drop | collection=dm_drop_docs | action=drop" in log


def test_mongo_clear_and_drop_of_a_missing_collection_are_not_errors(mongo_db, caplog):
    _, log = _run("mongo_clear_missing.xml", caplog)
    assert "OPERATION | mongodb.clear | collection=dm_never_created_a | action=clear | deleted_count=0" in log
    assert "OPERATION | mongodb.drop | collection=dm_never_created_b | action=drop" in log
    assert "dm_never_created_a" not in mongo_db.list_collection_names()


def test_mongo_clear_on_a_read_only_client_is_a_user_error_and_changes_nothing(mongo_db, caplog):
    name = "dm_clear_guarded_docs"
    mongo_db[name].drop()
    mongo_db[name].insert_one({"_id": 1})
    try:
        with pytest.raises(OperationError) as caught:
            _run("mongo_clear_read_only.xml", caplog)
        assert caught.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED
        assert mongo_db[name].count_documents({}) == 1
    finally:
        mongo_db[name].drop()


def test_mongo_clear_with_a_selector_is_refused_before_the_collection_is_touched(mongo_db, caplog):
    name = "dm_clear_untouched_docs"
    mongo_db[name].drop()
    mongo_db[name].insert_many([{"_id": 1}, {"_id": 2}])
    try:
        with pytest.raises(OperationError) as caught:
            _run("mongo_clear_invalid.xml", caplog)
        assert caught.value.issue_code is IssueCode.OPERATION_INTENT_INVALID
        assert mongo_db[name].count_documents({}) == 2
    finally:
        mongo_db[name].drop()
