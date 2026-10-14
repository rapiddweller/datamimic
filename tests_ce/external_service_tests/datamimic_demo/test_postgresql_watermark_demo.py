from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from shutil import copytree
from uuid import uuid4

import psycopg2
import pytest
from psycopg2 import sql

from datamimic_ce.engine.io.api import load_connection_profile
from datamimic_ce.engine.runtime.api import runtime_environment
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def postgres_demo(tmp_path: Path, request: pytest.FixtureRequest) -> Iterator[tuple[Path, dict]]:
    """Run an unchanged root with copied profiles and disposable databases."""
    path, systems = request.param
    demo = tmp_path / "demo"
    copytree(ROOT / path, demo)
    environment = "local" if runtime_environment() == "development" else "environment"
    config = load_connection_profile(ROOT / "tests_ce/external_service_tests/test_mongodb", environment)
    credentials = {key: config[f"postgres.db.{key}"] for key in ("host", "port", "user", "password")}
    admin = psycopg2.connect(**credentials, dbname=config["postgres.db.database"], connect_timeout=5)
    admin.autocommit = True
    databases = {}
    connections = {}
    try:
        profile = {}
        for system in systems:
            name = "ce_demo_" + uuid4().hex
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
            databases[system] = name
            connections[system] = psycopg2.connect(**credentials, dbname=name)
            profile.update({f"{system}.db.{key}": value for key, value in credentials.items()})
            profile.update({f"{system}.db.database": name, f"{system}.db.dbms": "postgresql"})
        for environment in ("local", "environment"):
            target = demo / "conf" / f"{environment}.env.properties"
            target.write_text("".join(f"{key}={value}\n" for key, value in profile.items()))
            target.chmod(0o600)
        yield demo, connections
    finally:
        for connection in connections.values():
            connection.close()
        for name in databases.values():
            with admin.cursor() as cursor:
                cursor.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
        admin.close()


def rows(connection, query: str) -> list[tuple]:
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


@pytest.mark.parametrize(
    "postgres_demo",
    [
        ("datamimic_ce/resources/demos/demo-watermark", ("source", "config", "target")),
        ("tests_ce/external_service_tests/datamimic_demo/k-watermark", ("source", "config", "target")),
    ],
    indirect=True,
)
def test_postgresql_watermark_demo_root(postgres_demo) -> None:
    demo, connections = postgres_demo
    before = datetime.now()
    DataMimicTest(demo, "datamimic.xml").test_with_timer()
    after = datetime.now()
    source = rows(connections["source"], "SELECT id, no, name, company, date FROM data ORDER BY id")
    target = rows(connections["target"], "SELECT id, no, name, company, date FROM data ORDER BY id")
    watermark = rows(connections["config"], "SELECT key_column, value_column FROM watermark")
    assert len(source) == len(target) == 10
    assert [row[0] for row in source] == list(range(1, 11))
    assert [(row[0], row[1], row[4]) for row in target] == [(row[0], row[1], row[4]) for row in source]
    assert all(isinstance(row[4], datetime) for row in source + target)
    assert all(row[2] and row[3] for row in target)
    assert any(original[2:4] != masked[2:4] for original, masked in zip(source, target, strict=True))
    assert len(watermark) == 1
    assert watermark[0][0] == "last_processed_datetime"
    final_timestamp = watermark[0][1]
    assert isinstance(final_timestamp, datetime)
    assert before <= final_timestamp <= after
    assert max(row[4] for row in source) <= final_timestamp
