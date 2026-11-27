# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""createTable on <generate>: the static rules, the column types, the SQLite create and drift check, the single-process
policy and the schema side effect. The end-to-end run and the Build rejections are scenario s59_create_table."""

import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.schema import CreateTable

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


def _generate(keys: tuple[str, ...] = (), ids: tuple[str, ...] = ("id",), **attributes: object) -> GenerateStatement:
    """A generate whose ``ids`` are written <id> and whose ``keys`` are written <key>, ids first."""
    attributes.setdefault("target", "CSV,db.upsert")
    attributes.setdefault("count", "1")
    stmt = GenerateStatement(GenerateModel(name="lines", **attributes), None)
    stmt.sub_statements = [
        *(_key(KeyModel(name=name, script=name), stmt, is_id=True) for name in ids),
        *(_key(KeyModel(name=name, script=name), stmt) for name in keys),
    ]
    return stmt


def _key(model: KeyModel, parent: GenerateStatement, *, is_id: bool = False) -> KeyStatement:
    key = KeyStatement(model, parent, is_id=is_id)
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
_SQLITE_DB = (("db", Dbms.SQLITE),)


# Static rules: the runtime and Build call the same checks.


def test_valid_create_table_has_no_problem():
    assert _generate(createTable="true").create_table_problem(nested=False, rdbms_clients=_SQLITE_DB) is None


def test_without_create_table_nothing_is_checked():
    assert _generate(target="CSV").create_table_problem(nested=True, rdbms_clients=()) is None


@pytest.mark.parametrize(
    ("ids", "nested", "reason"),
    [
        ((), False, "createTable needs an <id> for the primary key"),
        (("id",), True, "nested generate"),
    ],
    ids=["no_id", "nested"],
)
def test_rejected_create_table_names_the_broken_rule(ids, nested, reason):
    problem = _generate(("note",), ids=ids, createTable="true").create_table_problem(
        nested=nested, rdbms_clients=_SQLITE_DB
    )
    assert problem is not None and reason in problem[0]


def test_every_direct_id_is_a_primary_key_column_in_order():
    assert _generate(("note",), ids=("order_id", "line_no"), createTable="true").create_table == ("order_id", "line_no")


@pytest.mark.parametrize("value", [None, False], ids=["absent", "false"])
def test_without_create_table_an_id_is_a_plain_key(value):
    attributes = {} if value is None else {"createTable": value}
    stmt = _generate(("note",), **attributes)
    assert stmt.create_table is None
    assert stmt.create_table_problem(nested=True, rdbms_clients=_SQLITE_DB) is None


@pytest.mark.parametrize("target", ["CSV", "CSV,mem"], ids=["csv_only", "memstore_and_csv"])
def test_a_run_without_a_database_target_fails_before_the_first_row(tmp_path, monkeypatch, target):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datamimic.xml").write_text(
        f'<setup><memstore id="mem"/><generate name="lines" count="2" target="{target}" createTable="true">'
        '<id name="id" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    with pytest.raises(OperationError) as caught:
        DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
    assert caught.value.issue_code is IssueCode.OPERATION_CREATE_TABLE_INVALID
    assert "no database (RDBMS) client target" in str(caught.value)
    assert not list(tmp_path.glob("output/*/lines.csv")), "no row may be written"


@pytest.mark.parametrize("operation", ["update", "delete"])
def test_create_table_with_an_update_or_delete_target_is_rejected(operation):
    problem = _generate(createTable="true", target=f"db.{operation}").create_table_problem(
        nested=False, rdbms_clients=_SQLITE_DB
    )
    assert problem is not None and f"db.{operation} changes existing rows" in problem[0]


def test_a_later_page_with_a_new_field_fails_instead_of_dropping_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datamimic.xml").write_text(
        '<setup><database id="db" dbms="sqlite" database="sparse"/>'
        '<generate name="lines" count="4" pageSize="2" target="db" createTable="true">'
        '<id name="line_id" generator="IncrementGenerator"/>'
        '<key name="note" constant="late" condition="this.line_id &gt; 2"/></generate></setup>',
        encoding="utf-8",
    )
    with pytest.raises(OperationError) as caught:
        DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
    assert caught.value.issue_code is IssueCode.OPERATION_TABLE_DRIFT
    assert "a later page writes the field(s) note" in str(caught.value)
    assert "Table 'lines'" in str(caught.value)


def test_a_later_page_field_of_an_existing_table_is_not_blamed_on_a_table_created_from_page_one(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "db").mkdir()
    with closing(sqlite3.connect(tmp_path / "db" / "kept.sqlite")) as connection:
        connection.execute("CREATE TABLE lines (line_id INTEGER PRIMARY KEY, audit_user TEXT)")
        connection.commit()
    (tmp_path / "datamimic.xml").write_text(
        '<setup><database id="db" dbms="sqlite" database="kept"/>'
        '<generate name="lines" count="4" pageSize="2" target="db" createTable="true">'
        '<id name="line_id" generator="IncrementGenerator"/>'
        '<key name="audit_user" constant="secret-value" condition="this.line_id &gt; 2"/></generate></setup>',
        encoding="utf-8",
    )
    with pytest.raises(OperationError) as caught:
        DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
    message = str(caught.value)
    assert caught.value.issue_code is IssueCode.OPERATION_TABLE_DRIFT
    assert "Table 'lines'" in message
    assert "audit_user, which the first page did not write" in message
    assert "whether it created the table or found it" in message
    assert "table created from the first page does not have" not in message
    assert "secret-value" not in message


def test_a_field_in_every_page_passes_the_page_check(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datamimic.xml").write_text(
        '<setup><database id="db" dbms="sqlite" database="dense"/>'
        '<generate name="lines" count="4" pageSize="2" target="db" createTable="true">'
        '<id name="line_id" generator="IncrementGenerator"/><key name="note" constant="x"/></generate></setup>',
        encoding="utf-8",
    )
    DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()


@pytest.mark.parametrize("dbms", ["mysql", "mssql", "oracle"])
def test_a_run_refuses_a_dbms_that_cannot_make_the_types_before_it_connects(tmp_path, monkeypatch, dbms):
    monkeypatch.chdir(tmp_path)
    connected: list[str] = []
    monkeypatch.setattr(RdbmsClient, "_create_engine", lambda self: connected.append(dbms))
    (tmp_path / "datamimic.xml").write_text(
        f'<setup><database id="db" dbms="{dbms}" host="h" port="1" user="u" password="p" database="d"/>'
        '<generate name="lines" count="2" target="db" createTable="true">'
        '<id name="line_id" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    with pytest.raises(OperationError) as caught:
        DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
    assert caught.value.issue_code is IssueCode.OPERATION_CREATE_TABLE_INVALID
    assert f"createTable supports sqlite, postgresql, not {dbms}" in str(caught.value)
    assert connected == []


def test_a_run_with_no_rows_creates_no_table(tmp_path, monkeypatch):
    """The columns come from the first rows, so a generate that writes none has nothing to create."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "datamimic.xml").write_text(
        '<setup><database id="db" dbms="sqlite" database="empty"/>'
        '<generate name="lines" count="0" target="db" createTable="true">'
        '<id name="line_id" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
    assert not (tmp_path / "db" / "empty.sqlite").exists(), "no row, no column, no table and no connection"


def test_the_table_is_created_once_although_several_processes_and_pages_are_asked_for(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    created: list[str] = []
    real = RdbmsClient.ensure_table
    monkeypatch.setattr(
        RdbmsClient, "ensure_table", lambda self, *args: (created.append(args[0]), real(self, *args))[1]
    )
    (tmp_path / "datamimic.xml").write_text(
        '<setup><database id="db" dbms="sqlite" database="once"/>'
        '<generate name="lines" count="6" pageSize="2" numProcess="4" target="db" createTable="true">'
        '<id name="line_id" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    DataMimicTest(test_dir=tmp_path, filename="datamimic.xml").test_with_timer()
    assert created == ["lines"]


def test_create_table_on_a_clear_is_a_forbidden_attribute():
    stmt = GenerateStatement(GenerateModel(name="reset", target="db.clear", targetEntity="t", createTable="true"), None)
    stmt.sub_statements = []
    problem = stmt.operation_intent_problem(nested=False)
    assert problem is not None and problem[0].endswith("forbidden attributes: createTable")


@pytest.mark.parametrize("value", ["", "line_id", "maybe"])
def test_a_value_that_is_no_boolean_is_a_model_error(value):
    with pytest.raises(ValidationError, match="createTable"):
        GenerateModel(name="lines", count="1", target="db", createTable=value)


# Column types: key type= first, then the type of the non-null values; mixed types ask for type=.


def test_columns_follow_the_rows_and_take_declared_then_inferred_types():
    stmt = _generate(("note",), createTable="true")
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
        ([{"id": 1, "note": 10}, {"id": 2, "note": 10.5}], "column 'note' holds values of more than one type"),
        (
            [{"id": 1, "note": date(2026, 1, 2)}, {"id": 2, "note": datetime(2026, 1, 2, 3)}],
            "column 'note' holds values of more than one type",
        ),
    ],
    ids=["all_null", "unmapped_type", "key_not_written", "int_and_float", "date_and_datetime"],
)
def test_a_column_without_type_fails_and_asks_for_type(rows, reason):
    with pytest.raises(OperationError) as caught:
        _create_table_columns(_generate(("note",), createTable="true"), rows)
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
    assert "rdbms.create_table | table=lines | action=ensured" in dm_caplog.text
    assert "rdbms.create_table | table=lines | action=exists" in dm_caplog.text


@pytest.mark.parametrize("compatible", [True, False], ids=["matching", "drift"])
def test_ensure_table_validates_the_winner_of_an_overlapping_create(tmp_path, compatible):
    path = tmp_path / "t.db"
    loser = _client(path)
    winner = _client(path)
    winner_columns = _COLUMNS if compatible else _COLUMNS[:1]
    create_attempts = []

    @event.listens_for(loser.engine, "before_execute")
    def interleave(connection, statement, multiparams, params, execution_options):
        if isinstance(statement, CreateTable):
            create_attempts.append(statement)
            # Both clients found the table missing. Commit the winner's DDL before sending the loser's.
            winner.ensure_table("lines", winner_columns, ("id",))

    if compatible:
        loser.ensure_table("lines", _COLUMNS, ("id",))
        loser.insert("lines", [{"id": 1, "name": "first"}])
        assert winner.get("SELECT id, name FROM lines") == [(1, "first")]
    else:
        with pytest.raises(OperationError) as caught:
            loser.ensure_table("lines", _COLUMNS, ("id",))
        assert caught.value.issue_code is IssueCode.OPERATION_TABLE_DRIFT
        assert "missing columns name" in str(caught.value)
        assert [row[1] for row in winner.get("PRAGMA table_info(lines)")] == ["id"]
    assert len(create_attempts) == 1


def test_ensure_table_normalizes_a_sqlite_ddl_failure(tmp_path):
    client = _client(tmp_path / "t.db")
    client.execute_sql_script("CREATE TABLE owner (id INTEGER); CREATE INDEX lines ON owner (id)")
    with pytest.raises(OperationError) as caught:
        client.ensure_table("lines", _COLUMNS, ("id",))
    assert caught.value.issue_code is IssueCode.OPERATION_EXECUTION_FAILED
    assert caught.value.__context__ is None
    assert caught.value.__cause__.statement is None


@pytest.mark.parametrize(
    ("existing", "difference"),
    [
        ("CREATE TABLE lines (id INTEGER PRIMARY KEY, label TEXT)", "missing columns name"),
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


def test_build_ddl_names_the_schema_of_the_client():
    ddl = planned_create_table_ddl(Dbms.POSTGRESQL, "lines", _COLUMNS, ("id",), "sales")
    assert ddl.startswith("CREATE TABLE sales.lines (")


def test_an_existing_table_with_extra_columns_is_accepted(tmp_path):
    """A hand-written table may hold more columns: an insert leaves them to their default."""
    client = _client(tmp_path / "t.db")
    client.execute_sql_script("CREATE TABLE lines (id INTEGER PRIMARY KEY, name TEXT, audit_user TEXT)")
    client.ensure_table("lines", _COLUMNS, ("id",))


def test_a_column_name_that_differs_in_case_is_drift_because_an_insert_would_drop_its_value(tmp_path):
    client = _client(tmp_path / "t.db")
    client.execute_sql_script("CREATE TABLE lines (ID INTEGER PRIMARY KEY, Name TEXT)")
    with pytest.raises(OperationError) as caught:
        client.ensure_table("lines", _COLUMNS, ("id",))
    assert caught.value.issue_code is IssueCode.OPERATION_TABLE_DRIFT
    assert "missing columns id, name" in str(caught.value)


def test_ensure_table_is_blocked_on_a_read_only_connection(tmp_path):
    with pytest.raises(OperationError) as caught:
        _client(tmp_path / "t.db", read_only=True).ensure_table("lines", _COLUMNS, ("id",))
    assert caught.value.issue_code is IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED


@pytest.mark.parametrize("dbms", [Dbms.MYSQL, Dbms.MSSQL, Dbms.ORACLE])
def test_create_table_refuses_a_dbms_whose_types_it_cannot_make_exact(dbms):
    problem = _generate(createTable="true").create_table_problem(nested=False, rdbms_clients=(("db", dbms),))
    assert problem is not None and f"createTable supports sqlite, postgresql, not {dbms.value}" in problem[0]


def test_a_target_that_is_no_database_client_is_named_before_a_missing_id():
    """A MongoDB target has no table: the first message must say so, not ask for an <id> that would not help."""
    problem = _generate(ids=(), createTable="true", target="mongo").create_table_problem(nested=False, rdbms_clients=())
    assert problem is not None and "no database (RDBMS) client target" in problem[0]


@pytest.mark.parametrize(
    ("dbms", "text"),
    [(Dbms.SQLITE, "id BIGINT NOT NULL"), (Dbms.POSTGRESQL, "id BIGINT NOT NULL")],
)
def test_build_compiles_the_ddl_for_the_client_dbms_without_a_connection(dbms, text):
    ddl = planned_create_table_ddl(dbms, "lines", _COLUMNS, ("id",), None)
    assert ddl.startswith("CREATE TABLE lines (") and text in ddl and "PRIMARY KEY (id)" in ddl


# Once per run, and visible as its own side effect.


def test_create_table_runs_single_process():
    assert resolve_single_process(_generate(createTable="true"), 4) == 1
    assert resolve_single_process(_generate(), 4) is None


def test_create_table_is_a_schema_side_effect_per_database_target():
    setup = SetupStatement(SetupModel())
    setup.sub_statements = [_generate(createTable="true", targetEntity="journal")]
    effects = external_effects(setup, "datamimic.xml", frozenset(), _DB)
    assert [(item.kind, item.name) for item in effects if item.kind is ExternalEffectKind.SCHEMA] == [
        (ExternalEffectKind.SCHEMA, "db.journal")
    ]


# Build: the createTable rules that Build checks before the bounded run.


@pytest.mark.parametrize("dbms", ["mysql", "mssql", "oracle"])
def test_build_refuses_create_table_on_a_dbms_without_exact_types(tmp_path, dbms):
    from datamimic_ce.authoring.adapters.dryrun import neutralize_for_dry_run
    from datamimic_ce.engine.dsl.api import DescriptorParser

    xml = (
        f'<setup><database id="db" dbms="{dbms}" host="h" port="1" database="d" user="u" password="p"/>'
        '<generate name="lines" count="2" target="db.upsert" createTable="true">'
        '<id name="id" generator="IncrementGenerator"/></generate></setup>'
    )
    root = DescriptorParser.parse_xml(xml, tmp_path / "model.xml", None, "production", profile_loader=lambda *_: {})
    with pytest.raises(OperationError) as caught:
        neutralize_for_dry_run(root, max_count=2, allow_side_effects=False)
    assert caught.value.issue_code is IssueCode.OPERATION_CREATE_TABLE_INVALID
    assert f"createTable supports sqlite, postgresql, not {dbms}" in str(caught.value)


def test_build_rejects_create_table_without_a_database_target_with_i929(tmp_path, monkeypatch):
    from datamimic_ce.authoring import create_authoring_application
    from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RejectedBuild

    monkeypatch.chdir(tmp_path)
    (tmp_path / "acceptance").mkdir()
    (tmp_path / "datamimic.xml").write_text(
        '<setup rngSeed="1"><database id="ledger" dbms="sqlite" database="ledger"/>'
        '<generate name="lines" count="2" target="CSV" createTable="true">'
        '<id name="id" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    (tmp_path / "acceptance" / "build.json").write_text(
        '{"version": "5.0", "environment_bindings": [{"environment": "ledger", "family": "database"}], '
        '"expectations": [{"kind": "exact_count", "subject": {"kind": "product", "product": "lines"}, "count": 2}]}',
        encoding="utf-8",
    )
    built = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(built, RejectedBuild)
    issues = [str(item.ce_error.issue_code) for item in built.diagnostics if item.ce_error is not None]
    assert issues == ["I929"], [(str(item.code), item.message) for item in built.diagnostics]


def test_build_plans_a_composite_key_and_derives_no_per_field_unique(tmp_path, monkeypatch):
    """Each field of a composite key repeats; only the pair is unique. A per-field unique check would be wrong."""
    from datamimic_ce.authoring import create_authoring_application
    from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, ReadyBuild, ReadyWithGapsBuild

    monkeypatch.chdir(tmp_path)
    (tmp_path / "acceptance").mkdir()
    (tmp_path / "datamimic.xml").write_text(
        '<setup rngSeed="1"><database id="ledger" dbms="sqlite" database="ledger"/>'
        '<generate name="lines" count="4" target="ledger.upsert" createTable="true">'
        '<variable name="line" generator="IncrementGenerator"/>'
        '<id name="order_id" script="(line + 1) // 2"/><id name="line_no" script="line % 2"/>'
        '<key name="qty" constant="1"/>'
        "</generate></setup>",
        encoding="utf-8",
    )
    (tmp_path / "acceptance" / "build.json").write_text(
        '{"version": "5.0", "environment_bindings": [{"environment": "ledger", "family": "database"}], '
        '"expectations": [{"kind": "exact_count", "subject": {"kind": "product", "product": "lines"}, "count": 4}]}',
        encoding="utf-8",
    )
    built = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()
    # The only gap is the sink without an expectation, which this test does not declare.
    assert isinstance(built, ReadyBuild | ReadyWithGapsBuild), [
        (str(item.code), item.message) for item in built.diagnostics
    ]
    assert "PRIMARY KEY (order_id, line_no)" in built.planned_operations[0].ddl
    assert not [item for item in built.expectations.items if str(item.kind) == "unique"]
