"""Real DB source/capture/target regression; reducer and cleanup failures live in unit tests."""

import os
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree as ET

import psycopg2
import pytest
from psycopg2 import sql
from pymongo import MongoClient

from datamimic_ce.engine.io.api import load_connection_profile
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

FIELDS = (
    "source_id",
    "label",
    "plain_count",
    "captured_count",
    "closed_count",
    "default_alias",
    "registered_alias",
    "captured_closure",
    "worker_pid",
)


def _write_descriptor(directory: Path, backend: str, workers: int, target: bool, name: str, query: str) -> None:
    root = ET.Element("setup", multiprocessing=str(workers > 1), numProcess=str(workers))
    element, system = ("database", "postgres") if backend == "postgres" else ("mongodb", "mongodb")
    ET.SubElement(root, element, id="probe", system=system, environment="ownership")
    if target:
        ET.SubElement(root, element, id="sink", system=system, environment="ownership")
    ET.SubElement(root, "execute", type="python", uri="helpers.py")
    generate = ET.SubElement(
        root,
        "generate",
        name="rows",
        source="probe",
        selector=query,
        distribution="ordered",
        pageSize="2",
        target="sink" if target else "",
        targetEntity="written" if backend == "postgres" else name + "_written",
        mpPlatform="multiprocessing",
    )
    scripts = (
        "this.source_id",
        "this.label",
        "plain()",
        "captured()",
        "closed()",
        "captured.__defaults__[0] is probe",
        "alias is probe",
        "captured.__defaults__[0] is closed.__closure__[0].cell_contents",
        "worker_pid()",
    )
    for field, script in zip(FIELDS, scripts, strict=True):
        ET.SubElement(generate, "key", name=field, script=script)
    ET.ElementTree(root).write(directory / "probe.xml", encoding="unicode")
    (directory / "helpers.py").write_text(
        "alias = probe\n"
        "def worker_pid():\n    import os\n    return os.getpid()\n"
        "def plain():\n    return 6\n"
        f"def captured(bound=probe):\n    return bound.count_query_length({query!r})\n"
        "def make_capture(bound):\n"
        f"    def closure():\n        return bound.count_query_length({query!r})\n"
        "    return closure\nclosed = make_capture(probe)\n"
    )


@pytest.mark.parametrize(
    "backend,workers,target",
    [
        ("postgres", 1, False),
        ("postgres", 2, False),
        ("mongo", 1, False),
        ("mongo", 2, False),
        ("postgres", 2, True),
        ("mongo", 2, True),
    ],
)
def test_descriptor_clients_source_helpers_and_target(
    tmp_path: Path,
    backend: str,
    workers: int,
    target: bool,
) -> None:
    environment = "local" if get_settings().RUNTIME_ENVIRONMENT == "development" else "environment"
    profile = load_connection_profile(Path(__file__).parent / "test_mongodb", environment)
    name = "ce_ownership_" + uuid4().hex
    source_rows = [{"source_id": n, "label": f"value-{n}"} for n in range(1, 7)]
    if backend == "postgres":
        connection = psycopg2.connect(
            host=profile["postgres.db.host"],
            port=profile["postgres.db.port"],
            dbname=profile["postgres.db.database"],
            user=profile["postgres.db.user"],
            password=profile["postgres.db.password"],
            connect_timeout=5,
        )
        connection.autocommit = True
        query = f"SELECT source_id,label FROM {name}.rows ORDER BY source_id"
        # Profiles currently override explicit schema attributes (CE #291).
        profile["postgres.db.schema"] = name
    else:
        connection = MongoClient(
            host=profile["mongodb.mongo.host"],
            port=int(profile["mongodb.mongo.port"]),
            username=profile["mongodb.mongo.user"],
            password=profile["mongodb.mongo.password"],
            authSource=profile.get("mongodb.mongo.authSource", "admin"),
            serverSelectionTimeoutMS=5000,
        )
        database = connection[profile["mongodb.mongo.database"]]
        query = (
            f"aggregate: '{name}', pipeline: [{{'$sort': {{'source_id': 1}}}}, "
            "{'$project': {'_id': 0, 'source_id': 1, 'label': 1}}], cursor: {}"
        )
    created = False
    try:
        if backend == "postgres":
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
                created = True
                cursor.execute(
                    sql.SQL("CREATE TABLE {}.rows (source_id INTEGER PRIMARY KEY, label TEXT NOT NULL)").format(
                        sql.Identifier(name)
                    )
                )
                cursor.executemany(
                    sql.SQL("INSERT INTO {}.rows VALUES (%s,%s)").format(sql.Identifier(name)),
                    [(r["source_id"], r["label"]) for r in source_rows],
                )
                if target:
                    cursor.execute(
                        sql.SQL(
                            "CREATE TABLE {}.written (source_id INTEGER PRIMARY KEY, label TEXT NOT NULL, "
                            "plain_count INTEGER, captured_count INTEGER, closed_count INTEGER, "
                            "default_alias BOOLEAN, registered_alias BOOLEAN, captured_closure BOOLEAN, "
                            "worker_pid BIGINT)"
                        ).format(sql.Identifier(name))
                    )
        else:
            database.create_collection(name)
            created = True
            database[name].insert_many([dict(row) for row in source_rows])
        conf = tmp_path / "conf"
        conf.mkdir()
        config = conf / "ownership.env.properties"
        config.write_text("".join(f"{key}={value}\n" for key, value in profile.items()))
        config.chmod(0o600)
        _write_descriptor(tmp_path, backend, workers, target, name, query)
        engine = DataMimicTest(tmp_path, "probe.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()
        assert result is not None
        rows = result["rows"]
        assert [{"source_id": row["source_id"], "label": row["label"]} for row in rows] == source_rows
        for row in rows:
            assert type(row["source_id"]) is int and type(row["label"]) is str
            for field in ("plain_count", "captured_count", "closed_count"):
                assert type(row[field]) is int and row[field] == 6
            assert row["default_alias"] is (workers == 1)
            assert row["registered_alias"] is True
            assert row["captured_closure"] is True
            assert type(row["worker_pid"]) is int
        pids = {row["worker_pid"] for row in rows}
        if workers == 1:
            assert pids == {os.getpid()}
        else:
            assert len(pids) == 2 and os.getpid() not in pids
        if target:
            if backend == "postgres":
                with connection.cursor() as cursor:
                    cursor.execute(
                        sql.SQL("SELECT {} FROM {}.written ORDER BY source_id").format(
                            sql.SQL(",").join(map(sql.Identifier, FIELDS)), sql.Identifier(name)
                        )
                    )
                    written = [dict(zip(FIELDS, values, strict=True)) for values in cursor.fetchall()]
            else:
                written = list(database[name + "_written"].find({}, {"_id": 0}).sort("source_id", 1))
            assert written == rows
            assert [{field: type(value) for field, value in row.items()} for row in written] == [
                {field: type(value) for field, value in row.items()} for row in rows
            ]
    finally:
        try:
            if created and backend == "postgres":
                with connection.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(name)))
                    cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=%s)", (name,))
                    assert cursor.fetchone() == (False,)
            elif created:
                database.drop_collection(name)
                database.drop_collection(name + "_written")
                assert name not in database.list_collection_names()
                assert name + "_written" not in database.list_collection_names()
        finally:
            connection.close()
