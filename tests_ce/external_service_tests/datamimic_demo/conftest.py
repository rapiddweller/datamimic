from collections.abc import Iterator
from pathlib import Path
from shutil import copytree
from uuid import uuid4

import psycopg2
import pytest
from psycopg2 import sql

from datamimic_ce.engine.io.api import load_connection_profile
from datamimic_ce.engine.runtime.api import runtime_environment

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
