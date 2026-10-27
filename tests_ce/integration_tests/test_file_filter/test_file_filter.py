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


def test_build_refuses_kept_rows_above_the_limit_with_the_count_rule(tmp_path: Path) -> None:
    """20 kept rows exceed the default limit 10: the run refuses the count instead of capping it silently."""
    from datamimic_ce.authoring.bootstrap import create_authoring_application
    from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RejectedBuild

    iterate = (
        '<iterate name="rows" source="data/fixtures/many.ent.csv" distribution="ordered" '
        'where="int(amount) % 2 == 0" target="ConsoleExporter"/>'
    )
    built = create_authoring_application(_project(tmp_path, iterate), descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(built, RejectedBuild)
    assert [(str(d.code), d.ce_error.issue_code if d.ce_error else None) for d in built.diagnostics] == [
        ("child_execution", IssueCode.TASK_COUNT_ABOVE_BOUNDED_LIMIT)
    ]


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
