# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Scenario projects that need PostgreSQL or MongoDB (issue #411, S7 and X6). Same contract as tests_ce/scenarios: Build
is ready, a run gives the expected rows, a second run gives the same rows, and each negative is rejected with its
diagnostic. A project holds db/seed.sql (PostgreSQL) and db/seed.json (MongoDB): the test loads them before Build,
because Build refuses an <execute> step and reads the tables as they are. The state checks read the services."""

import json
import re
import shutil
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import quote_plus

import pytest
from pymongo import MongoClient
from pymongo.database import Database
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.coverage import CoverageGapKind
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ENTRY_PATH,
    BuildResult,
    ReadyBuild,
    ReadyWithGapsBuild,
    RejectedBuild,
)
from datamimic_ce.engine.dsl.api import parse_properties
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.errors.base import TaskConfigError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_ROOT = Path(__file__).resolve().parent
_PROJECTS = sorted(path.parent for path in _ROOT.glob("*/scenario.json"))


def _scenario(project: Path) -> dict:
    return json.loads((project / "scenario.json").read_text(encoding="utf-8"))


def _properties(project: Path) -> dict[str, str]:
    name = (
        "local.env.properties" if get_settings().RUNTIME_ENVIRONMENT == "development" else "environment.env.properties"
    )
    return parse_properties(project / "conf" / name)


@pytest.fixture
def pg(request: pytest.FixtureRequest) -> Iterator[Engine]:
    props = _properties(request.getfixturevalue("project"))
    url = (
        f"postgresql+psycopg2://{props['postgresql.db.user']}:{quote_plus(props['postgresql.db.password'])}"
        f"@{props['postgresql.db.host']}:{props['postgresql.db.port']}/{props['postgresql.db.database']}"
    )
    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def mongo(request: pytest.FixtureRequest) -> Iterator[Database]:
    props = _properties(request.getfixturevalue("project"))
    client = MongoClient(
        host=props["mongodb.mongo.host"],
        port=int(props["mongodb.mongo.port"]),
        username=props["mongodb.mongo.user"],
        password=props["mongodb.mongo.password"],
        authSource=props.get("mongodb.mongo.authSource", "admin"),
    )
    yield client[props["mongodb.mongo.database"]]
    client.close()


def _seed(project: Path, pg: Engine, mongo: Database) -> None:
    sql = project / "db" / "seed.sql"
    if sql.exists():
        with pg.begin() as connection:
            for statement in sql.read_text(encoding="utf-8").split(";\n"):
                if statement.strip():
                    connection.execute(text(statement))
    documents = project / "db" / "seed.json"
    if documents.exists():
        for collection, rows in json.loads(documents.read_text(encoding="utf-8")).items():
            mongo[collection].drop()
            mongo[collection].insert_many(rows)


def _build(project: Path) -> BuildResult:
    return create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()


def _run(project: Path) -> dict[str, list[object]]:
    engine = DataMimicTest(test_dir=project, filename=PROJECT_ENTRY_PATH, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result() or {}


def _without_document_ids(rows: dict[str, list[object]]) -> dict[str, list[object]]:
    """A MongoDB readback keeps the `_id` that the service made for each document: a new value on every run."""
    return {
        name: [
            {key: value for key, value in row.items() if key != "_id"} if isinstance(row, dict) else row
            for row in items
        ]
        for name, items in rows.items()
    }


def _assert_state(project: Path, pg: Engine, mongo: Database) -> None:
    """The delivered state, read from the services and not from the project."""
    if project.name == "s50_postgres_readback":
        with pg.connect() as connection:
            rows = connection.execute(text("SELECT id, status, amount_cents FROM dm_s50_orders ORDER BY id")).all()
        assert [row[0] for row in rows] == list(range(1, 13))
        assert {row[1] for row in rows} <= {"new", "paid", "shipped"}
        assert sum(row[2] for row in rows) == 64254
    elif project.name == "s51_mongo_readback":
        documents = list(mongo["dm_s51_orders"].find({}, {"_id": 0}).sort("id", 1))
        assert [document["id"] for document in documents] == list(range(1, 13))
        assert {document["status"] for document in documents} <= {"new", "paid", "shipped"}
        assert all(100 <= document["amount_cents"] <= 9900 for document in documents)
    else:
        raw = list(mongo["dm_x6_raw_orders"].find({}, {"_id": 0}).sort("order_id", 1))
        with pg.connect() as connection:
            rows = connection.execute(text("SELECT order_id, amount_cents, status FROM dm_x6_orders ORDER BY order_id"))
            delivered = rows.all()
        assert len(raw) == len(delivered) == 12
        for document, (order_id, cents, status) in zip(raw, delivered, strict=True):
            # `cents` is the amount before it became a noisy text: the transform must give it back
            assert (document["order_id"], document["cents"], document["status_raw"].strip().lower()) == (
                order_id,
                cents,
                status,
            )
            assert document["amount_text"] != str(cents), "the source text must be noisy"


@pytest.fixture
def project(request: pytest.FixtureRequest, tmp_path: Path) -> Path:
    return shutil.copytree(request.param, tmp_path / request.param.name, ignore=shutil.ignore_patterns("scenario.json"))


@pytest.mark.parametrize("project", _PROJECTS, ids=lambda path: path.name, indirect=True)
def test_scenario_builds_runs_and_replays(project: Path, pg: Engine, mongo: Database) -> None:
    scenario = _scenario(_ROOT / project.name)
    _seed(project, pg, mongo)

    built = _build(project)
    diagnostics = [(str(item.code), item.message) for item in built.diagnostics]
    assert isinstance(built, (ReadyBuild, ReadyWithGapsBuild)), diagnostics
    expected_gaps = tuple(CoverageGapKind(kind) for kind in scenario.get("gaps", []))
    assert built.coverage.open_gaps == expected_gaps, diagnostics
    assert built.outcome == ("ready_with_gaps" if expected_gaps else "ready"), diagnostics

    first = _run(project)
    counts = {name: len(rows) for name, rows in first.items() if name in scenario["products"]}
    assert counts == scenario["products"]
    _assert_state(project, pg, mongo)
    assert _without_document_ids(_run(project)) == _without_document_ids(first), "a second run must give identical rows"
    _assert_state(project, pg, mongo)


_NEGATIVES = [(path, negative) for path in _PROJECTS for negative in _scenario(path)["negatives"]]


@pytest.mark.parametrize(
    "project, negative",
    [pytest.param(path, negative, id=f"{path.name}/{negative['name']}") for path, negative in _NEGATIVES],
    indirect=["project"],
)
def test_negative_is_rejected_with_named_diagnostic(project: Path, negative: dict, pg: Engine, mongo: Database) -> None:
    _seed(project, pg, mongo)
    patch = negative["patch"]
    target = project / patch["file"]
    content = target.read_text(encoding="utf-8")
    assert content.count(patch["old"]) == 1, f"{patch['file']} must contain the old text exactly once"
    target.write_text(content.replace(patch["old"], patch["new"]), encoding="utf-8")

    rejected = _build(project)
    assert isinstance(rejected, RejectedBuild), "Build accepted a variant that must be rejected"
    codes = [str(item.code) for item in rejected.diagnostics]
    assert negative["diagnostic"] in codes, f"expected {negative['diagnostic']}, Build reported {codes}"
    if "expected" in negative:
        named = [str(item.expected) for item in rejected.diagnostics if str(item.code) == negative["diagnostic"]]
        assert negative["expected"] in named, f"expected {negative['expected']!r}, Build reported {named}"
    if "run_error" in negative:  # the variant must also stop a normal run, with the message of its <assert>
        with pytest.raises(TaskConfigError, match=re.escape(negative["run_error"])):
            _run(project)
