# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""createTable on <generate>: the static rules, the column types, the SQLite create and drift check, the single-process
policy and the schema side effect. The end-to-end run and the Build rejections are scenario s59_create_table."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine

from datamimic_ce.authoring.adapters.external_effects import external_effects
from datamimic_ce.authoring.domain.project_run import ExternalEffectKind
from datamimic_ce.engine.dsl.api import GenerateStatement, KeyStatement, SetupStatement
from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
from datamimic_ce.engine.dsl.model.setup.setup_model import SetupModel
from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.api import ColumnKind, planned_create_table_ddl
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.runtime.tasks.generate.policies.single_process_policy import resolve_single_process
from datamimic_ce.engine.runtime.tasks.generate.workers.generate_worker import _create_table_columns
from datamimic_ce.errors import IssueCode, OperationError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DB = frozenset({"db"})


def _generate(keys: tuple[str, ...] = ("id",), **attributes: object) -> GenerateStatement:
    attributes.setdefault("target", "CSV,db.upsert")
    attributes.setdefault("count", "1")
    stmt = GenerateStatement(GenerateModel(name="lines", **attributes), None)
    stmt.sub_statements = [_key(KeyModel(name=name, script=name), stmt) for name in keys]
    return stmt


def _key(model: KeyModel, parent: GenerateStatement) -> KeyStatement:
    key = KeyStatement(model, parent)
    key.sub_statements = []
    return key


def _typed(name: str, type_: str, stmt: GenerateStatement) -> KeyStatement:
    return _key(KeyModel(name=name, script=name, type=type_), stmt)


def _client(path: Path, read_only: bool = False) -> RdbmsClient:
    client = RdbmsClient(
        RdbmsConnectionConfig(
            dbms=Dbms.SQLITE,
            host=None,
            port=None,
            user=None,
            password=None,
            database="test",
            db_schema=None,
            read_only=read_only,
        )
    )
    client.engine = create_engine(f"sqlite:///{path}")
    return client


_COLUMNS = (("id", ColumnKind.INTEGER), ("name", ColumnKind.TEXT))


# Static rules: the runtime and Build call the same checks.


def test_valid_create_table_has_no_problem():
    assert _generate(createTable="id").create_table_problem(nested=False) is None


def test_without_create_table_nothing_is_checked():
    assert _generate(target="CSV").create_table_problem(nested=True) is None


@pytest.mark.parametrize(
    ("attributes", "nested", "reason"),
    [
        ({"createTable": "id, line_no"}, False, "line_no are not a <key>"),
        ({"createTable": "id"}, True, "nested generate"),
    ],
    ids=["unknown_key", "nested"],
)
def test_rejected_create_table_names_the_broken_rule(attributes, nested, reason):
    problem = _generate(**attributes).create_table_problem(nested=nested)
    assert problem is not None and reason in problem[0]


@pytest.mark.parametrize("target", ["CSV", "CSV,mem"], ids=["csv_only", "memstore_and_csv"])
def test_a_run_without_a_database_target_fails_before_the_first_row(tmp_path, monkeypatch, target):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datamimic.xml").write_text(
        f'<setup><memstore id="mem"/><generate name="lines" count="2" target="{target}" createTable="id">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    with pytest.raises(OperationError) as caught:
        DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
    assert caught.value.issue_code is IssueCode.OPERATION_CREATE_TABLE_INVALID
    assert "no database (RDBMS) client target" in str(caught.value)
    assert not list(tmp_path.glob("output/*/lines.csv")), "no row may be written"


def test_create_table_on_a_clear_is_a_forbidden_attribute():
    stmt = GenerateStatement(GenerateModel(name="reset", target="db.clear", targetEntity="t", createTable="id"), None)
    stmt.sub_statements = []
    problem = stmt.operation_intent_problem(nested=False)
    assert problem is not None and problem[0].endswith("forbidden attributes: createTable")


@pytest.mark.parametrize("value", ["", " , ", "id,", "id, id"])
def test_empty_or_repeated_column_list_is_a_model_error(value):
    with pytest.raises(ValidationError, match="createTable"):
        GenerateModel(name="lines", count="1", target="db", createTable=value)


# Column types: key type= first, then the first non-null value.


def test_columns_follow_the_rows_and_take_declared_then_inferred_types():
    stmt = _generate(("id", "note"), createTable="id")
    stmt.sub_statements = [*stmt.sub_statements[:1], _typed("note", "string", stmt)]
    rows = [
        {"id": 1, "note": None, "flag": True, "amount": Decimal("1.5"), "rate": 0.5},
        {"id": 2, "note": None, "flag": None, "on": date(2026, 1, 2), "at": datetime(2026, 1, 2, 3), "text": "x"},
    ]
    assert _create_table_columns(stmt, rows) == (
        ("id", ColumnKind.INTEGER),
        ("note", ColumnKind.TEXT),
        ("flag", ColumnKind.BOOLEAN),
        ("amount", ColumnKind.DECIMAL),
        ("rate", ColumnKind.FLOAT),
        ("on", ColumnKind.DATE),
        ("at", ColumnKind.DATETIME),
        ("text", ColumnKind.TEXT),
    )


@pytest.mark.parametrize(
    ("rows", "reason"),
    [
        ([{"id": 1, "note": None}], "column 'note' holds only null values"),
        ([{"id": 1, "note": timedelta(days=1)}], "column 'note' holds a timedelta value"),
        ([{"note": "x"}], "primary-key column(s) id are not in the written rows"),
    ],
    ids=["all_null", "unmapped_type", "key_not_written"],
)
def test_a_column_without_type_fails_and_asks_for_type(rows, reason):
    with pytest.raises(OperationError) as caught:
        _create_table_columns(_generate(("id", "note"), createTable="id"), rows)
    assert caught.value.issue_code is IssueCode.OPERATION_CREATE_TABLE_INVALID
    assert reason in str(caught.value)
    assert "set type=" in str(caught.value)


# The RDBMS client: create once, never alter, fail on drift.


def test_ensure_table_creates_a_missing_table_and_accepts_it_again(tmp_path, dm_caplog):
    client = _client(tmp_path / "t.db")
    client.ensure_table("lines", _COLUMNS, ("id",))
    client.ensure_table("LINES", _COLUMNS, ("id",))  # the second run finds the table, without case
    client.upsert("lines", [{"id": 1, "name": "a"}])
    client.upsert("lines", [{"id": 1, "name": "b"}])
    assert client.get("SELECT id, name FROM lines") == [(1, "b")]
    assert "rdbms.create_table | table=lines | action=created" in dm_caplog.text
    assert "rdbms.create_table | table=lines | action=exists" in dm_caplog.text


@pytest.mark.parametrize(
    ("existing", "difference"),
    [
        ("CREATE TABLE lines (id INTEGER PRIMARY KEY, label TEXT)", "missing columns name; extra columns label"),
        ("CREATE TABLE lines (id INTEGER, name TEXT)", "primary key (none) instead of (id)"),
        ("CREATE TABLE lines (id INTEGER, name TEXT PRIMARY KEY)", "primary key (name) instead of (id)"),
    ],
    ids=["other_columns", "no_primary_key", "other_primary_key"],
)
def test_an_existing_table_that_differs_fails_with_the_difference_and_is_not_altered(tmp_path, existing, difference):
    client = _client(tmp_path / "t.db")
    client.execute_sql_script(existing)
    with pytest.raises(OperationError) as caught:
        client.ensure_table("lines", _COLUMNS, ("id",))
    assert caught.value.issue_code is IssueCode.OPERATION_TABLE_DRIFT
    assert difference in str(caught.value)
    assert client.get("SELECT sql FROM sqlite_master WHERE name = 'lines'") == [(existing,)]


def test_ensure_table_is_blocked_on_a_read_only_connection(tmp_path):
    with pytest.raises(OperationError) as caught:
        _client(tmp_path / "t.db", read_only=True).ensure_table("lines", _COLUMNS, ("id",))
    assert caught.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED


@pytest.mark.parametrize(
    ("dbms", "text"),
    [(Dbms.SQLITE, "id BIGINT NOT NULL"), (Dbms.POSTGRESQL, "id BIGINT NOT NULL")],
)
def test_build_compiles_the_ddl_for_the_client_dbms_without_a_connection(dbms, text):
    ddl = planned_create_table_ddl(dbms, "lines", _COLUMNS, ("id",))
    assert ddl.startswith("CREATE TABLE lines (") and text in ddl and "PRIMARY KEY (id)" in ddl


# Once per run, and visible as its own side effect.


def test_create_table_runs_single_process():
    assert resolve_single_process(_generate(createTable="id"), 4) == 1
    assert resolve_single_process(_generate(), 4) is None


def test_create_table_is_a_schema_side_effect_per_database_target():
    setup = SetupStatement(SetupModel())
    setup.sub_statements = [_generate(createTable="id", targetEntity="journal")]
    effects = external_effects(setup, "datamimic.xml", frozenset(), _DB)
    assert [(item.kind, item.name) for item in effects if item.kind is ExternalEffectKind.SCHEMA] == [
        (ExternalEffectKind.SCHEMA, "db.journal")
    ]
