# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""where= and columns= on <generate>/<iterate> file sources (#447). The descriptors beside this module are the
cases; this module runs them and compares rows."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from datamimic_ce.errors import IssueCode
from datamimic_ce.errors.base import UserErrorBase
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent
_ROOT = _DIR.parents[2]
_KEPT = ["2", "3", "5"]  # amounts 1000, 1001 and 2500; 999 and 150 are out


def _run(filename: str) -> dict[str, list[dict[str, object]]]:
    engine = DataMimicTest(_DIR, filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result() or {}


def _refusal(filename: str, directory: Path = _DIR) -> UserErrorBase:
    engine = DataMimicTest(directory, filename, capture_test_result=True)
    with pytest.raises(UserErrorBase) as raised:
        engine.test_with_timer()
    return raised.value


@pytest.mark.parametrize("product", ["rows_ent", "rows_json", "rows_xml", "rows_xlsx", "rows_fcw", "rows_dbunit"])
def test_every_file_format_keeps_the_same_rows_and_only_the_listed_column(product: str) -> None:
    rows = _run("formats.xml")[product]
    assert [str(row["id"]) for row in rows] == _KEPT
    assert all(set(row) == {"id"} for row in rows)


def test_a_weighted_csv_at_generate_is_a_table_and_where_reads_its_weight_column() -> None:
    # weight >= 2 removes order 3 (weight 1) from the amount filter; no weighting happens at <generate>.
    assert _run("formats.xml")["rows_wgt"] == [{"id": "2"}, {"id": "5"}]


def test_columns_order_readable_variables_empty_list_and_overriding_key() -> None:
    result = _run("columns.xml")
    first = result["ordered_columns"][0]
    assert list(first) == ["status", "id", "doubled", "same"]
    assert first == {"status": "open", "id": "1", "doubled": 1998, "same": True}
    assert [row["parent_amount"] for row in result["line"]] == ["999", "1000", "1001", "150", "2500"]
    assert result["no_columns"][0] == {"amount": 1000}
    assert [row.get("note") for row in result["sparse_json"]] == [None, None, "only this row has a note", None, None]
    assert [set(row) for row in result["sparse_json"]][2] == {"id", "note"}
    assert result["empty_file"] == []
    assert result["duplicates"] == [{"id": "1"}, {"id": "1"}]


def test_statements_on_one_file_with_other_conditions_keep_their_own_rows() -> None:
    """The kept-row count belongs to the condition: a same-name statement must not reuse the count of the first."""
    result = _run("same_file_other_where.xml")
    assert [row["id"] for row in result["closed_rows"]] == ["3", "5"]
    assert [row["id"] for row in result["open_rows"]] == ["1", "2", "4"]
    for product in ("rows", "child"):
        assert [row["id"] for row in result[product]] == ["3", "5", "1", "2", "4"], product


@pytest.mark.parametrize(
    ("filename", "code"),
    [
        ("refused_memstore.xml", IssueCode.GENERATE_ROW_SELECTION_FILE_ONLY),
        ("refused_source_scripted.xml", IssueCode.GENERATE_ROW_SELECTION_SOURCE_SCRIPTED),
        ("refused_default_source_scripted.xml", IssueCode.GENERATE_ROW_SELECTION_SOURCE_SCRIPTED),
        ("refused_unknown_column.xml", IssueCode.SOURCE_COLUMN_UNKNOWN),
        ("refused_where_not_bool.xml", IssueCode.CONDITION_NOT_BOOLEAN),
        ("refused_where_draws.xml", IssueCode.TASK_EXPRESSION_EVAL_FAILED),
        ("refused_where_parent.xml", IssueCode.TASK_EXPRESSION_EVAL_FAILED),
    ],
)
def test_refused_row_selection_names_its_catalog_code(filename: str, code: IssueCode) -> None:
    assert _refusal(filename).issue_code is code


_ROW_RULE = "where reads one row and must not read the clock or draw random values"


def test_unseeded_where_refuses_a_random_draw_with_the_row_rule() -> None:
    assert _ROW_RULE in str(_refusal("refused_where_draws.xml"))


@pytest.mark.parametrize("setup", ['rngSeed="1"', ""], ids=["seeded", "unseeded"])
@pytest.mark.parametrize(
    "read",
    [
        "datetime.datetime.now()",
        "datetime.datetime.utcnow()",
        "datetime.datetime.today()",
        "datetime.date.today()",
        "pd.Timestamp.now()",
        "pd.Timestamp.utcnow()",
        "pd.Timestamp.today()",
        "np.random.random()",
        "os.urandom(1)",
        "os.getrandom(1)",
        "uuid.uuid1()",
        "uuid.uuid4()",
        "random.SystemRandom()",
        "random.random()",
        "fake.boolean()",
    ],
)
def test_where_refuses_every_clock_read_and_draw_with_the_row_rule(tmp_path: Path, setup: str, read: str) -> None:
    """A seeded run would see the fixed anchor and an unseeded run the wall clock: where must see neither."""
    _project(tmp_path, f'<iterate name="rows" source="data/fixtures/orders.ent.csv" where="{read} is None"/>', setup)
    error = _refusal("datamimic.xml", tmp_path)
    assert error.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert _ROW_RULE in str(error)


@pytest.mark.parametrize("setup", ['rngSeed="1"', ""], ids=["seeded", "unseeded"])
@pytest.mark.parametrize("read", ["time.time()", "time.monotonic()"])
def test_where_has_no_time_module(tmp_path: Path, setup: str, read: str) -> None:
    """Expressions know no time module, so where cannot reach that clock either."""
    _project(tmp_path, f'<iterate name="rows" source="data/fixtures/orders.ent.csv" where="{read} &gt; 0"/>', setup)
    assert _refusal("datamimic.xml", tmp_path).issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED


def test_where_keeps_date_arithmetic_without_the_clock(tmp_path: Path) -> None:
    where = (
        "datetime.date.fromisoformat('2026-03-02') - datetime.timedelta(days=1) &gt;= datetime.date(2026, 3, 1) "
        "and datetime.datetime(2026, 1, 1).year == 2026 and int(amount) &gt;= 1000"
    )
    _project(
        tmp_path,
        f'<iterate name="rows" source="data/fixtures/orders.ent.csv" distribution="ordered" '
        f'where="{where}" columns="id"/>',
        "",
    )
    assert [row["id"] for row in _run_xml(tmp_path, "")] == _KEPT


def test_unknown_column_message_names_the_statement_and_the_column() -> None:
    assert "<generate> 'rows': columns= names 'amount_cents', which no row of the source has" in str(
        _refusal("refused_unknown_column.xml")
    )


def test_where_on_a_database_client_is_refused_before_any_read() -> None:
    dirs = (_DIR / "output", _DIR / "db", _ROOT / "db")
    for directory in dirs:
        shutil.rmtree(directory, ignore_errors=True)
    try:
        error = _refusal("refused_client.xml")
        assert error.issue_code is IssueCode.GENERATE_ROW_SELECTION_FILE_ONLY
        assert "not database client 'db'" in str(error)
    finally:
        for directory in dirs:
            shutil.rmtree(directory, ignore_errors=True)


def test_two_processes_keep_the_same_rows_as_one_process() -> None:
    multi = _run("mp.xml")["rows"]
    single = _run("single.xml")["rows"]
    assert [row["id"] for row in multi] == [row["id"] for row in single] == [str(n) for n in range(3, 41, 3)]
    # Control: the multiprocess run really used two worker processes.
    assert len({row["pid"] for row in multi}) == 2
    assert len({row["pid"] for row in single}) == 1


def test_seeded_where_run_replays_identically_across_hash_seeds() -> None:
    script = (
        "import json, sys; from pathlib import Path; "
        "from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest; "
        "e = DataMimicTest(Path(sys.argv[1]), 'replay.xml', capture_test_result=True); e.test_with_timer(); "
        "print(json.dumps(e.capture_result()['rows']))"
    )
    outputs = []
    for hash_seed in ("1", "2", "3"):
        env = {**os.environ, "PYTHONHASHSEED": hash_seed, "PYTHONPATH": str(_ROOT)}
        done = subprocess.run(
            [sys.executable, "-c", script, str(_DIR)], env=env, capture_output=True, text=True, check=True
        )
        outputs.append(json.loads(done.stdout.strip().splitlines()[-1]))
    assert outputs[0] == outputs[1] == outputs[2]
    rows = outputs[0]
    assert len(rows) == 15 and all(int(row["id"]) % 2 == 0 for row in rows)
    assert len({row["id"] for row in rows}) == 15  # the random pool is the 20 kept rows, drawn without repeats


def _project(tmp_path: Path, iterate: str, setup: str = 'rngSeed="1"') -> Path:
    shutil.copytree(_DIR / "data", tmp_path / "data")
    (tmp_path / "acceptance").mkdir()
    (tmp_path / "acceptance" / "build.json").write_text('{"version": "5.0", "expectations": []}', encoding="utf-8")
    (tmp_path / "datamimic.xml").write_text(f"<setup {setup}>{iterate}</setup>", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("source", "extra"),
    [
        ("data/fixtures/orders.ent.csv", ""),
        ("data/fixtures/orders.json", ""),
        ("data/fixtures/orders.dbunit.xml", 'sourceEntity="orders"'),
    ],
)
def test_build_proves_the_capture_with_the_runtime_kept_count(tmp_path: Path, source: str, extra: str) -> None:
    """Build has no second count for where=: the bounded run counts the kept rows, and the capture is complete."""
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.capture import CaptureStatus
    from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RunRequest

    iterate = (
        f'<iterate name="rows" source="{source}" {extra} distribution="ordered" where="int(amount) &gt;= 1000" '
        'target="ConsoleExporter"/>'
    )
    project = _project(tmp_path, iterate)
    xml = (project / "datamimic.xml").read_text(encoding="utf-8")
    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).dry_run(
        RunRequest(xml=xml, descriptor_path=PROJECT_ENTRY_PATH)
    )
    (product,) = result.products
    assert result.ok and product.capture is not None and product.capture.status is CaptureStatus.COMPLETE
    assert [str(row["id"]) for row in product.rows] == _KEPT == [str(row["id"]) for row in _run_xml(tmp_path, xml)]


def _run_xml(tmp_path: Path, xml: str) -> list[dict[str, object]]:
    engine = DataMimicTest(tmp_path, "datamimic.xml", capture_test_result=True)
    engine.test_with_timer()
    return (engine.capture_result() or {})["rows"]


@pytest.mark.parametrize(
    ("statement", "attribute", "remediation", "actual"),
    [
        (
            '<iterate name="rows" source="data/fixtures/many.ent.csv" distribution="ordered" '
            'where="int(amount) % 2 == 0" target="ConsoleExporter"/>',
            "where",
            "Raise max_count to at least the number of rows that where= keeps, or narrow the where= condition.",
            {"requested": 20, "limit": 10},
        ),
        # Control: a count expression keeps its location, its fix and no value, because the descriptor computed it.
        (
            '<generate name="rows" count="{5 * 4}" target="ConsoleExporter"/>',
            "count",
            "Raise max_count to at least the evaluated count, or lower the count expression.",
            None,
        ),
    ],
)
def test_build_refuses_kept_rows_above_the_limit_with_the_count_rule(
    tmp_path: Path, statement: str, attribute: str, remediation: str, actual: dict[str, int] | None
) -> None:
    """20 kept rows exceed the default limit 10: the run refuses the count instead of capping it silently, and the
    diagnostic names where=, the kept rows and the limit."""
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RejectedBuild

    built = create_authoring_application(_project(tmp_path, statement), descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(built, RejectedBuild)
    (diagnostic,) = built.diagnostics
    assert (
        diagnostic.ce_error is not None and diagnostic.ce_error.issue_code is IssueCode.TASK_COUNT_ABOVE_BOUNDED_LIMIT
    )
    assert diagnostic.model_dump(mode="json", exclude={"ce_error"}) == {
        "code": "child_execution",
        "message": f"Task Count Above Bounded Limit at descriptor/datamimic.xml/generate/{attribute}.",
        "phase": "evidence",
        "path": ["descriptor", "datamimic.xml", "generate", attribute],
        "severity": "error",
        "remediation": remediation,
        "expected": None,
        "actual": actual,
        "allowed_values": None,
    }


@pytest.mark.parametrize(
    ("attributes", "code"),
    [
        ('sourceScripted="True" where="int(amount) &gt; 1"', IssueCode.GENERATE_ROW_SELECTION_SOURCE_SCRIPTED),
        ('columns="id, amount_cents"', IssueCode.SOURCE_COLUMN_UNKNOWN),
    ],
)
def test_dry_run_and_build_report_the_same_catalog_code(tmp_path: Path, attributes: str, code: IssueCode) -> None:
    """The refusals are runtime facts (they need the file or the resolved setup default), so lint stays silent and
    dry-run and Build both report the bounded run's catalog code."""
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.requests import (
        PROJECT_ENTRY_PATH,
        LintRequest,
        RejectedBuild,
        RunRequest,
    )

    shutil.copytree(_DIR / "data", tmp_path / "data")
    (tmp_path / "acceptance").mkdir()
    (tmp_path / "acceptance" / "build.json").write_text('{"version": "5.0", "expectations": []}', encoding="utf-8")
    xml = (
        f'<setup rngSeed="1"><iterate name="rows" source="data/fixtures/orders.ent.csv" distribution="ordered" '
        f"{attributes} "
        'target="ConsoleExporter"/></setup>'
    )
    (tmp_path / "datamimic.xml").write_text(xml, encoding="utf-8")
    app = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH)

    assert app.lint(LintRequest(xml=xml)).ok
    dry = app.dry_run(RunRequest(xml=xml, descriptor_path=PROJECT_ENTRY_PATH))
    built = app.build()
    assert isinstance(built, RejectedBuild)
    for diagnostics in (dry.diagnostics, built.diagnostics):
        assert [(str(d.code), d.ce_error.issue_code if d.ce_error else None) for d in diagnostics] == [
            ("child_execution", code)
        ]


@pytest.mark.parametrize(
    ("attributes", "rule"),
    [
        ('where="int(amount) &gt; 1"', "DM214"),
        ('columns="id"', "DM214"),
        ('source="data/fixtures/orders.ent.csv" offset="1" where="int(amount) &gt; 1"', "DM218"),
        ('source="data/fixtures/orders.ent.csv" columns="id, id"', "columns"),
        ('source="data/fixtures/orders.ent.csv" columns="id,,status"', "columns"),
        ('source="data/fixtures/orders.ent.csv" where="  "', "where"),
    ],
)
def test_lint_refuses_the_static_row_selection_rules(tmp_path: Path, attributes: str, rule: str) -> None:
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.requests import LintRequest

    xml = f'<setup rngSeed="1"><generate name="rows" count="1" {attributes} target="ConsoleExporter"/></setup>'
    result = create_authoring_application(_DIR).lint(LintRequest(xml=xml))
    assert not result.ok
    # A field rule has no lint id: the parser reports the descriptor field by its attribute path.
    found = [str(item.code) for item in result.diagnostics] + [
        str(item.path[-1]) for item in result.diagnostics if str(item.code) == "descriptor"
    ]
    assert rule in found, result.diagnostics


@pytest.mark.parametrize(
    ("where", "rules"),
    [
        # A set of strings iterates in hash-seed order: the kept rows change with PYTHONHASHSEED under rngSeed.
        ("list({'open', 'closed', 'x1', 'y2'})[0] == status", {"DM319"}),
        ("__status__ == 'open'", {"DM314"}),
        ("sorted({'open', 'closed', 'x1', 'y2'})[0] == status", set()),
    ],
)
def test_lint_scans_where_like_a_script(where: str, rules: set[str]) -> None:
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.requests import LintRequest

    xml = (
        '<setup rngSeed="1"><iterate name="rows" source="data/fixtures/orders.ent.csv" '
        f'where="{where}" target="ConsoleExporter"/></setup>'
    )
    codes = {str(item.code) for item in create_authoring_application(_DIR).lint(LintRequest(xml=xml)).diagnostics}
    assert codes & {"DM314", "DM319"} == rules


@pytest.mark.parametrize(
    ("where", "rows", "phrase"),
    [
        ('where="int(amount) &gt;= 1000" ', 3, "kept by where= from"),
        ("", 5, "available from"),
    ],
)
def test_count_above_the_rows_names_the_kept_rows(tmp_path: Path, where: str, rows: int, phrase: str) -> None:
    import logging

    class _Records(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.messages: list[str] = []

        def emit(self, record: logging.LogRecord) -> None:
            self.messages.append(record.getMessage())

    _project(
        tmp_path,
        f'<iterate name="rows" source="data/fixtures/orders.ent.csv" distribution="ordered" {where}count="9"/>',
    )
    records = _Records()
    logging.getLogger("DATAMIMIC").addHandler(records)
    try:
        _run_xml(tmp_path, "")
    finally:
        logging.getLogger("DATAMIMIC").removeHandler(records)
    assert [message for message in records.messages if "count=9" in message] == [
        f"<generate> 'rows': count=9 exceeds the {rows} rows {phrase} source 'data/fixtures/orders.ent.csv' and "
        f'cyclic is off — only {rows} rows will be generated. Set cyclic="True" to wrap the source, or drop count=.'
    ]


@pytest.mark.parametrize("text", ["", "   "])
def test_an_empty_columns_text_names_no_column(text: str) -> None:
    from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel

    assert GenerateModel.column_names(text) == ()
    assert GenerateModel.column_names(" status , id ") == ("status", "id")


@pytest.mark.parametrize(("kept", "ready"), [(10, True), (11, False)])
def test_build_limit_boundary_for_kept_rows(tmp_path: Path, kept: int, ready: bool) -> None:
    """The default limit is 10: ten kept rows prove the capture, eleven stop the run with the count rule."""
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, ReadyBuild

    iterate = (
        f'<iterate name="rows" source="data/fixtures/many.ent.csv" distribution="ordered" '
        f'where="int(amount) &lt;= {kept}" columns="id" target="ConsoleExporter"/>'
    )
    project = _project(tmp_path, iterate)
    (project / "acceptance" / "build.json").write_text(
        json.dumps(
            {
                "version": "5.0",
                "expectations": [
                    {"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": kept}
                ],
            }
        ),
        encoding="utf-8",
    )
    built = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(built, ReadyBuild) is ready, built.diagnostics


_KEEP = 'source="data/fixtures/orders.ent.csv" distribution="ordered" where="int(amount) &gt;= 1000"'
_TWO = '<variable name="v" source="data/fixtures/two.ent.csv" distribution="ordered"/>'
_TICKS = 'start="2026-01-01T00:00:00+00:00" end="2026-01-01T00:00:03+00:00" interval="PT1S"'
_TWO_CYCLIC = '<variable name="v" source="data/fixtures/two.ent.csv" distribution="ordered" cyclic="True"/>'


@pytest.mark.parametrize(
    ("generate", "status", "observed", "reason"),
    [
        # The three kept rows are emitted in full.
        (f'<generate name="rows" {_KEEP}/>', "complete", 3, "where="),
        # A shorter non-cyclic variable source ends the generate after two of the three kept rows.
        (f'<generate name="rows" {_KEEP}>{_TWO}</generate>', "unknown", 2, "where="),
        # A cyclic variable wraps: the loop never emits more rows than where= kept.
        (f'<generate name="rows" {_KEEP}>{_TWO_CYCLIC}</generate>', "complete", 3, "where="),
        # No row passes: no row is read from the variable and the empty capture is complete.
        (
            '<generate name="rows" source="data/fixtures/orders.ent.csv" where="int(amount) &gt; 99999">'
            f"{_TWO}</generate>",
            "complete",
            0,
            "where=",
        ),
        # An explicit count is the requested count: the underrun is visible without the runtime count.
        (f'<generate name="rows" count="3" {_KEEP}>{_TWO}</generate>', "unknown", 2, "static count"),
        # Without where= the source length is the requested count: the same underrun stays unknown.
        (
            f'<generate name="rows" source="data/fixtures/orders.ent.csv" distribution="ordered">{_TWO}</generate>',
            "unknown",
            2,
            "file source",
        ),
        # A count expression and a count range have no static requested count either.
        (f'<generate name="rows" count="{{1 + 2}}">{_TWO}</generate>', "unknown", 2, "count"),
        (f'<generate name="rows" minCount="3" maxCount="4">{_TWO}</generate>', "unknown", 2, "count"),
        ('<generate name="rows" count="{1 + 2}"/>', "complete", 3, "dynamic count"),
        # A time series resolves series times ticks rows: two series of three ticks are six rows.
        (f'<generate name="rows" count="{{2}}" {_TICKS}/>', "complete", 6, "dynamic count"),
        (f'<generate name="rows" count="{{2}}" {_TICKS}>{_TWO}</generate>', "unknown", 2, "count"),
    ],
)
def test_build_compares_the_emitted_rows_with_the_runtime_count(
    tmp_path: Path, generate: str, status: str, observed: int, reason: str
) -> None:
    """Build is one process. A generator or variable source that ends early stops the generate without an error,
    so a capture is complete only when it holds every row that the run resolved for the generate."""
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RunRequest

    project = _project(tmp_path, generate)
    xml = (project / "datamimic.xml").read_text(encoding="utf-8")
    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).dry_run(
        RunRequest(xml=xml, descriptor_path=PROJECT_ENTRY_PATH)
    )
    (product,) = result.products
    assert product.capture is not None
    assert (product.capture.status.value, product.capture.observed) == (status, observed), product.capture
    assert reason in product.capture.reason


@pytest.mark.parametrize(("variable", "status", "observed"), [(_TWO, "unknown", 4), (_TWO_CYCLIC, "complete", 6)])
def test_build_adds_the_kept_rows_of_a_nested_generate_across_its_parents(
    tmp_path: Path, variable: str, status: str, observed: int
) -> None:
    """Each of the two parents keeps three rows: the runtime count of the child is the sum, six."""
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RunRequest

    generate = f'<generate name="parents" count="2"><generate name="rows" {_KEEP}>{variable}</generate></generate>'
    project = _project(tmp_path, generate)
    xml = (project / "datamimic.xml").read_text(encoding="utf-8")
    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).dry_run(
        RunRequest(xml=xml, descriptor_path=PROJECT_ENTRY_PATH)
    )
    child = {product.name: product for product in result.products}["rows"]
    assert child.capture is not None
    assert (child.capture.status.value, child.capture.observed) == (status, observed), child.capture


def test_a_failed_assert_keeps_the_underrun_unknown_in_the_stopped_capture(tmp_path: Path) -> None:
    """A failed assert stops the run and Build keeps the products that completed before it: their capture evidence
    compares the emitted rows with the runtime count as on success."""
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RejectedBuild

    generate = (
        f'<generate name="rows" {_KEEP}>{_TWO}</generate>'
        '<generate name="gate" count="1"><key name="n" script="1"/>'
        '<assert condition="this.n &gt; 1" message="stop here"/></generate>'
    )
    built = create_authoring_application(_project(tmp_path, generate), descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(built, RejectedBuild)
    rows = {product.name: product for product in built.evidence}["rows"]
    assert rows.capture is not None
    assert (rows.capture.status.value, rows.capture.observed) == ("unknown", 2), rows.capture
