from collections.abc import Iterator
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
        ("datamimic_ce/resources/demos/demo-db-mapping", ("mapping",)),
        ("tests_ce/external_service_tests/datamimic_demo/demo-db-mapping", ("mapping",)),
    ],
    indirect=True,
)
def test_postgresql_mapping_demo_root(postgres_demo) -> None:
    import csv

    demo, connections = postgres_demo
    engine = DataMimicTest(demo, "datamimic.xml", capture_test_result=True)
    engine.test_with_timer()
    connection = connections["mapping"]
    with (demo / "data/business_mapping.ent.csv").open() as source:
        expected = list(csv.DictReader(source, delimiter="|"))
    actual = rows(
        connection,
        'SELECT "idTop", "idSub", "countryCode", city, "postCode", description, title, title_description FROM business_mapping ORDER BY "idTop"',
    )
    assert actual == [
        (
            int(row["idTop"]),
            int(row["idSub"]),
            row["countryCode"],
            row["city"],
            row["postCode"],
            row["description"],
            row["title"],
            row["title_description"],
        )
        for row in sorted(expected, key=lambda row: int(row["idTop"]))
    ]
    assert len(actual) == 1000
    with pytest.raises(psycopg2.errors.NotNullViolation):
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO business_mapping (city) VALUES ('missing-key')")
    connection.rollback()
    result = engine.capture_result()
    assert result is not None
    transactions = result["transaction_record"]
    assert len(transactions) == 100
    for transaction in transactions:
        assert len(transaction["transaction_details"]) == 10
        for detail in transaction["transaction_details"]:
            assert any(
                (detail["account_id"], detail["branch_id"], transaction["city"]) == (row[0], row[1], row[3])
                for row in actual
            )
