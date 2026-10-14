from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from shutil import copytree
from uuid import uuid4

import psycopg2
import pytest
from psycopg2 import sql

from datamimic_ce.engine.dsl.api import parse_properties
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def postgres_demo(tmp_path: Path, request: pytest.FixtureRequest) -> Iterator[tuple[Path, dict]]:
    """Run an unchanged root with copied profiles and disposable databases."""
    path, systems = request.param
    demo = tmp_path / "demo"
    copytree(ROOT / path, demo)
    config = parse_properties(ROOT / "local.env.properties")
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
            if "c-simple-anonymization" in path:
                # This older fixture owns explicit source/target SQL schemas.
                profile[f"{system}.db.schema"] = system
                with connections[system].cursor() as cursor:
                    cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(system)))
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
        ("datamimic_ce/resources/demos/demo-database", ("db",)),
        ("tests_ce/external_service_tests/datamimic_demo/b-simple-database", ("source",)),
        ("datamimic_ce/resources/demos/demo-masking", ("source", "target")),
        ("tests_ce/external_service_tests/datamimic_demo/c-simple-anonymization", ("source", "target")),
    ],
    indirect=True,
)
def test_postgresql_database_demo_roots(postgres_demo) -> None:
    demo, connections = postgres_demo
    # Preparation must also reset tables that already contain related rows.
    for _ in range(2):
        DataMimicTest(demo, "datamimic.xml").test_with_timer()
    if len(connections) == 1:
        connection = next(iter(connections.values()))
        assert rows(connection, "SELECT count(*) FROM customer") == [(10,)]
        users = rows(connection, 'SELECT id, tc_creation, email, customer_id FROM "user" ORDER BY id')
        expected_users = 100 if "db" in connections else 10
        assert len(users) == expected_users
        assert [row[0] for row in users] == list(range(1, expected_users + 1))
        assert all(isinstance(row[1], datetime) and row[2] and 1 <= row[3] <= 10 for row in users)
        assert rows(connection, "SELECT count(*) FROM product") == [(0,)]
    else:
        source, target = connections["source"], connections["target"]
        customers = rows(source, "SELECT id, name, tc_creation FROM customer ORDER BY id")
        assert len(customers) == 10
        assert rows(target, "SELECT id, name, tc_creation FROM customer ORDER BY id") == [
            (identifier, name + "_mask", created) for identifier, name, created in customers
        ]
        users = rows(source, 'SELECT id, full_name, email, tc_creation, customer_id FROM "user" ORDER BY id')
        masked = rows(target, 'SELECT id, full_name, email, tc_creation, customer_id FROM "user" ORDER BY id')
        assert len(users) == len(masked) == 10
        for original, obfuscated in zip(users, masked, strict=True):
            assert obfuscated == (original[0], original[1] + "_mask", "*" * len(original[2]), original[3], original[4])
            assert isinstance(obfuscated[3], datetime)
            assert 1 <= obfuscated[4] <= 10
