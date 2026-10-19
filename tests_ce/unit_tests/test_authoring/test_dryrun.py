# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Dry-run: capped, capture-only execution with the safety gates."""

import tempfile
from pathlib import Path

import pytest

import datamimic_ce.authoring.adapters.dryrun as dryrun_module
from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, AuthoringSystemDiagnosticCode
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.engine.io.exporters.formats.json_exporter import JsonExporter
from datamimic_ce.engine.runtime.api import create_run_session
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.errors.codes import ErrorCode, IssueCode

_PIPELINE = """<setup rngSeed="1">
    <memstore id="mem"/>
    <generate name="users" count="500" target="mem,CSV,ConsoleExporter">
        <key name="id" generator="IncrementGenerator"/>
        <key name="age" type="int" min="18" max="99"/>
    </generate>
    <generate name="from_mem" source="mem" type="users" distribution="ordered" target="JSON"/>
</setup>"""
_FIXTURES = Path(__file__).parent / "fixtures"
_SMOKE_EXPORT_MATRIX = _FIXTURES / "issue_227_smoke_export_matrix.xml"
_JSON_WRITE = JsonExporter._write_data_to_buffer


def _short_write_json(self: JsonExporter, data: list[dict], worker_id: int, chunk_idx: int) -> None:
    _JSON_WRITE(self, data[:-1], worker_id, chunk_idx)


def _execute_source(xml, **kwargs):
    return CeBoundedExecutor().execute(BoundedExecutionRequest(xml=xml, **kwargs))


def _execute_file(path, **kwargs):
    return CeBoundedExecutor(AuthoringWorkspaceContext(path.parent)).execute(
        BoundedExecutionRequest(xml=path.read_text(encoding="utf-8"), **kwargs)
    )


def _capture_here(xml, *, smoke_export=False):
    with tempfile.TemporaryDirectory() as directory:
        descriptor = Path(directory) / "model.xml"
        descriptor.write_text(xml, encoding="utf-8")
        return dryrun_module._run_engine_capture(descriptor, 10, False, smoke_export)


def _observe_smoke_artifact(directory):
    receipt = _observe_smoke_artifact.receipt
    try:
        smoke_dir = Path(directory.name)
        if smoke_dir.name.startswith("datamimic_smoke_"):
            for artifact in smoke_dir.glob("temp_result_*_exporter_*_product_*/*"):
                receipt.write_bytes(artifact.read_bytes())
    finally:
        _observe_smoke_artifact.original_cleanup(directory)


def test_dry_run_caps_counts_strips_targets_keeps_memstore(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)  # any accidental artifact would land here
    result = _execute_source(_PIPELINE, max_count=7)
    assert result.ok, [d.message for d in result.diagnostics]

    by_name = {p.name: p for p in result.captured.products}
    assert len(by_name["users"].rows) == 7  # capped from 500
    assert len(by_name["from_mem"].rows) == 7  # memstore target kept -> pipeline works
    assert len(by_name["users"].rows) == 7  # response sampling cannot shrink internal capture
    assert by_name["users"].rows[0]["id"] == 1

    # no artifacts anywhere: CSV/JSON/Console were stripped
    assert not list(tmp_path.rglob("*.csv")) and not list(tmp_path.rglob("output"))


def test_dry_run_sample_preserves_nested_structure() -> None:
    # Agents verify intent from the sample ("is reviews a LIST of dicts with a rating?").
    # Nested structures must survive as dict/list, never be stringified.
    xml = """<setup rngSeed="1">
        <generate name="products" count="5" target="JSON">
            <key name="sku" pattern="[A-Z]{3}-[0-9]{4}"/>
            <nestedKey name="reviews" type="list" minCount="2" maxCount="2">
                <key name="rating" type="int" min="1" max="5"/>
            </nestedKey>
        </generate>
    </setup>"""
    result = _execute_source(xml, max_count=5)
    assert result.ok, [d.message for d in result.diagnostics]
    row = result.captured.products[0].rows[0]
    assert isinstance(row["reviews"], list) and len(row["reviews"]) == 2
    assert isinstance(row["reviews"][0], dict) and 1 <= row["reviews"][0]["rating"] <= 5


def test_dry_run_lint_gate_blocks_broken_descriptor(tmp_path) -> None:
    workspace = AuthoringWorkspaceContext(tmp_path)
    result = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(
        "<setup><generate name='a' pagesize='5' target='ConsoleExporter'/></setup>"
    )
    assert not result.ok
    assert result.diagnostics


def test_dry_run_refuses_execute_without_allow() -> None:
    xml = """<setup rngSeed="1">
        <execute uri="script/x.sql"/>
        <generate name="a" count="1" target="ConsoleExporter"><key name="x" constant="1"/></generate>
    </setup>"""
    result = _execute_source(xml)
    assert not result.ok
    assert [d.code for d in result.diagnostics] == [AuthoringRuleId.SIDE_EFFECT]


@pytest.mark.parametrize(
    "body",
    [
        '<include uri="included.xml"/>',
        '<generate name="rows" count="1"><include uri="included.xml"/></generate>',
    ],
)
def test_dry_run_refuses_execute_in_included_descriptor(tmp_path: Path, body: str) -> None:
    marker = tmp_path / "executed.txt"
    script = tmp_path / "marker.scr.py"
    script.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )
    included = tmp_path / "included.xml"
    included.write_text('<setup><execute uri="marker.scr.py"/></setup>', encoding="utf-8")
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(f"<setup>{body}</setup>", encoding="utf-8")

    result = _execute_file(descriptor)

    assert not marker.exists()
    assert not result.ok
    assert [diagnostic.code for diagnostic in result.diagnostics] == [AuthoringRuleId.SIDE_EFFECT]


def test_dry_run_refuses_unbounded_include_even_when_side_effects_allowed(tmp_path: Path) -> None:
    (tmp_path / "included.xml").write_text(
        '<setup><generate name="rows" count="20"><key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text('<setup><include uri="included.xml"/></setup>', encoding="utf-8")

    result = _execute_file(descriptor, max_count=1, allow_side_effects=True)

    assert not result.ok and [diagnostic.code for diagnostic in result.diagnostics] == [AuthoringRuleId.SIDE_EFFECT]


def test_dry_run_keeps_properties_include(tmp_path: Path) -> None:
    (tmp_path / "values.properties").write_text("limit=1\n", encoding="utf-8")
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup><include uri="values.properties"/>'
        '<generate name="rows" count="1"><key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )

    result = _execute_file(descriptor)

    assert result.ok


def test_dry_run_maps_runtime_error_to_dm002() -> None:
    # lints clean (source file simply missing at runtime) -> DM002 with hint
    xml = """<setup rngSeed="1">
        <generate name="a" count="3" source="missing.csv" distribution="ordered" target="ConsoleExporter"/>
    </setup>"""
    result = _execute_source(xml)
    assert not result.ok
    assert [d.code for d in result.diagnostics] == [AuthoringSystemDiagnosticCode.CHILD_EXECUTION]
    assert result.diagnostics[0].remediation


def test_dm004_flags_zero_row_output() -> None:
    # An empty/mis-wired descriptor runs clean but generates nothing — surface it.
    empty = _execute_source("<setup></setup>")
    assert not empty.ok  # no crash, but no useful output either
    assert [d.code for d in empty.diagnostics] == [AuthoringSystemDiagnosticCode.NOT_EXECUTED]
    assert empty.diagnostics[0].severity == "error"

    # a real descriptor that produces rows must NOT get DM004
    real = _execute_source(
        '<setup rngSeed="1"><generate name="g" count="3" target="JSON">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>'
    )
    assert real.ok and len(real.captured.products[0].rows) == 3
    assert not [d for d in real.diagnostics if d.code is AuthoringSystemDiagnosticCode.NOT_EXECUTED]


def test_smoke_export_passes_and_leaves_no_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run = _execute_source(_SMOKE_EXPORT_MATRIX.read_text(encoding="utf-8"), smoke_export=True)
    assert run.ok, [(d.code, d.message) for d in run.diagnostics]
    assert {product.name: len(product.rows) for product in run.captured.products} == {"audit": 2, "items": 4}
    assert run.smoke_export.applicable_exporters == 9
    assert run.smoke_export.attempted_exporters == 9
    assert run.smoke_export.failed_exporters == 0
    assert not list(tmp_path.iterdir())  # smoke writes never leave the temp dir


@pytest.mark.parametrize(
    ("exporter", "xml", "expected"),
    [
        (
            "CSV",
            '<setup rngSeed="17"><generate name="rows" count="2" target="CSV">'
            '<key name="id" generator="IncrementGenerator"/><key name="label" constant="x"/>'
            "</generate></setup>",
            b"id|label\r\n1|x\r\n2|x\r\n",
        ),
        (
            "CSV",
            '<setup rngSeed="17" defaultSeparator=""><generate name="rows" count="2" target="CSV">'
            '<key name="id" generator="IncrementGenerator"/><key name="label" constant="x"/>'
            "</generate></setup>",
            b"id|label\r\n1|x\r\n2|x\r\n",
        ),
        (
            "CSV",
            '<setup rngSeed="17" defaultSeparator=";"><generate name="rows" count="2" target="CSV">'
            '<key name="id" generator="IncrementGenerator"/><key name="label" constant="x"/>'
            "</generate></setup>",
            b"id;label\r\n1;x\r\n2;x\r\n",
        ),
        (
            "CSV",
            '<setup rngSeed="17" defaultSeparator="||"><generate name="rows" count="2" target="CSV(delimiter=\';\')">'
            '<key name="id" generator="IncrementGenerator"/><key name="label" constant="x"/>'
            "</generate></setup>",
            b"id;label\r\n1;x\r\n2;x\r\n",
        ),
        (
            "CSV",
            '<setup rngSeed="17"><generate name="parents" count="2" target="ConsoleExporter">'
            '<key name="id" generator="IncrementGenerator"/><generate name="children" count="1" target="CSV">'
            '<key name="parent_id" script="parent.id"/><key name="label" constant="x"/>'
            "</generate></generate></setup>",
            b"parent_id|label\r\n1|x\r\n2|x\r\n",
        ),
        (
            "TXT",
            '<setup rngSeed="17"><generate name="rows" count="2" target="TXT">'
            '<key name="id" generator="IncrementGenerator"/></generate></setup>',
            b"rows: {'id': 1}\nrows: {'id': 2}\n",
        ),
        (
            "TXT",
            '<setup rngSeed="17" defaultSeparator=";" defaultLineSeparator=";">'
            '<generate name="rows" count="2" target="TXT">'
            '<key name="id" generator="IncrementGenerator"/></generate></setup>',
            b"rows: {'id': 1};rows: {'id': 2};",
        ),
        (
            "TXT",
            '<setup rngSeed="17" defaultLineSeparator="\\r\\n">'
            '<generate name="rows" count="2" target="TXT">'
            '<key name="id" generator="IncrementGenerator"/></generate></setup>',
            b"rows: {'id': 1}\r\nrows: {'id': 2}\r\n",
        ),
        (
            "TXT",
            '<setup rngSeed="17" defaultSeparator="||" defaultLineSeparator="\\r\\n">'
            '<generate name="rows" count="2" target="TXT(separator=\':\', line_terminator=\';\')">'
            '<key name="id" generator="IncrementGenerator"/></generate></setup>',
            b"rows: {'id': 1};rows: {'id': 2};",
        ),
    ],
)
def test_smoke_export_uses_setup_defaults_and_matches_runtime_artifact(
    tmp_path: Path,
    monkeypatch,
    exporter: str,
    xml: str,
    expected: bytes,
) -> None:
    monkeypatch.chdir(tmp_path)
    _observe_smoke_artifact.receipt = tmp_path / "smoke-artifact.bin"
    _observe_smoke_artifact.original_cleanup = tempfile.TemporaryDirectory.cleanup
    monkeypatch.setattr(tempfile.TemporaryDirectory, "cleanup", _observe_smoke_artifact)
    smoked = _capture_here(xml, smoke_export=True)
    assert isinstance(smoked, dryrun_module._WorkerSuccess), smoked
    assert not smoked.smoke_diagnostics
    assert (tmp_path / "smoke-artifact.bin").read_bytes() == expected
    assert {path.name for path in tmp_path.iterdir()} == {"smoke-artifact.bin"}

    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text(xml, encoding="utf-8")
    create_run_session(RunRequest(descriptor_path=descriptor, task_id="real_export", test_mode=True)).execute()
    artifacts = sorted((tmp_path / "output" / "real_export").glob(f"*.{exporter.lower()}"))
    assert len(artifacts) == 1
    assert artifacts[0].read_bytes() == expected


def test_smoke_export_rejects_multichar_setup_csv_separator_like_runtime(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    xml = """<setup rngSeed="17" defaultSeparator="||">
        <generate name="rows" count="2" target="CSV">
            <key name="id" generator="IncrementGenerator"/>
            <key name="label" constant="x"/>
        </generate>
    </setup>"""

    smoked = _execute_source(xml, smoke_export=True)

    assert not smoked.ok
    assert [diagnostic.code for diagnostic in smoked.diagnostics] == [AuthoringSystemDiagnosticCode.CHILD_EXECUTION]
    assert smoked.smoke_export.failed_exporters == 1
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text(xml, encoding="utf-8")
    with pytest.raises(ValueError, match="delimiter.*1-character"):
        create_run_session(RunRequest(descriptor_path=descriptor, task_id="real_export")).execute()
    assert not list(tmp_path.glob("output/*/*.csv"))


@pytest.mark.parametrize(
    ("fixture", "expected_rows"),
    [
        ("issue_227_smoke_export_xml_single_record.xml", 1),
        ("issue_227_smoke_export_xml_flattened_items.xml", 1),
        ("issue_227_smoke_export_txt_terminator.xml", 3),
        ("issue_227_smoke_export_txt_crlf.xml", 3),
        ("issue_227_smoke_export_txt_separator_value.xml", 3),
        ("issue_227_smoke_export_csv_quotechar.xml", 3),
    ],
)
def test_smoke_export_reads_configured_final_artifact_dialects(
    tmp_path: Path,
    monkeypatch,
    fixture: str,
    expected_rows: int,
) -> None:
    monkeypatch.chdir(tmp_path)
    result = _execute_source((_FIXTURES / fixture).read_text(encoding="utf-8"), smoke_export=True)
    assert result.ok, [(diagnostic.code, diagnostic.message) for diagnostic in result.diagnostics]
    assert len(result.captured.products[0].rows) == expected_rows
    assert not list(tmp_path.iterdir())


def test_smoke_export_honors_target_encoding(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = _execute_source(
        (_FIXTURES / "issue_227_smoke_export_ascii_encoding.xml").read_text(encoding="utf-8"),
        smoke_export=True,
    )
    assert not result.ok
    assert any(diagnostic.code is AuthoringSystemDiagnosticCode.CHILD_EXECUTION for diagnostic in result.diagnostics)
    assert not list(tmp_path.iterdir())


def test_issue_256_fixed_width_smoke_export_reads_rows_with_target_encoding(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = _execute_source(
        (_FIXTURES / "issue_256_fixed_width_latin1.xml").read_text(encoding="utf-8"),
        smoke_export=True,
    )

    assert result.ok, [(d.code, d.message) for d in result.diagnostics]
    assert {product.name: len(product.rows) for product in result.captured.products} == {"rows": 3}
    assert result.smoke_export.applicable_exporters == 1
    assert result.smoke_export.attempted_exporters == 1
    assert result.smoke_export.failed_exporters == 0
    assert not list(tmp_path.iterdir())


def test_issue_256_ndjson_chunk_one_smoke_export_counts_each_row_once(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = _execute_source(
        (_FIXTURES / "issue_256_json_ndjson_chunk_one.xml").read_text(encoding="utf-8"),
        smoke_export=True,
    )

    assert result.ok, [(d.code, d.message) for d in result.diagnostics]
    assert {product.name: len(product.rows) for product in result.captured.products} == {"rows": 3}
    assert result.smoke_export.applicable_exporters == 1
    assert result.smoke_export.attempted_exporters == 1
    assert result.smoke_export.failed_exporters == 0
    assert not list(tmp_path.iterdir())


def test_smoke_export_catches_unserializable_value_plain_dry_run_does_not(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    xml = """<setup rngSeed="1"><generate name="batches" count="2">
      <key name="batch_id" generator="IncrementGenerator"/>
      <generate name="blobs" count="2" target="JSON"><key name="payload" script="re.compile('exotic')"/></generate>
    </generate></setup>"""

    def refuse_smoke(*args):
        pytest.fail("invalid native capture must be rejected before any exporter runs")

    monkeypatch.setattr(dryrun_module, "_smoke_export", refuse_smoke)
    plain = _capture_here(xml)
    smoked = _capture_here(xml, smoke_export=True)
    assert isinstance(plain, dryrun_module._WorkerFailure)
    assert isinstance(smoked, dryrun_module._WorkerFailure)
    assert "unsupported passive value" in plain.message
    assert not list(tmp_path.iterdir())


def test_smoke_export_compares_buffered_exporter_row_count(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    xml = (_FIXTURES / "issue_227_smoke_rows.xml").read_text(encoding="utf-8").strip()
    positive = _execute_source(xml, smoke_export=True)
    assert positive.ok and positive.smoke_export.failed_exporters == 0
    monkeypatch.setattr(JsonExporter, "_write_data_to_buffer", _short_write_json)
    negative = _capture_here(xml, smoke_export=True)
    assert isinstance(negative, dryrun_module._WorkerSuccess)
    assert negative.smoke_export.failed_exporters == 1
    assert "wrote 2 of 3 captured rows" in negative.smoke_diagnostics[0]["message"]
    assert not list(tmp_path.iterdir())


def test_dm002_runtime_errors_carry_actionable_hints() -> None:
    """Runtime crashes must teach the fix, not just echo the traceback — the loop
    depends on it. Each signature maps to a specific hint, not the generic fallback."""
    empty_memstore = """<setup rngSeed="1"><memstore id="mem"/>
        <iterate name="r" source="mem" type="nope" distribution="ordered" count="3" target="ConsoleExporter"/>
    </setup>"""
    result = _capture_here(empty_memstore)
    assert isinstance(result, dryrun_module._WorkerFailure)
    hint = result.fix_hint
    assert "memstore" in hint.lower() and "before" in hint.lower()
    assert "Fix the reported runtime error" not in hint  # not the generic fallback

    bad_script = """<setup rngSeed="1">
        <generate name="o" count="3" target="ConsoleExporter"><key name="x" script="ghost * 3"/></generate>
    </setup>"""
    result2 = _capture_here(bad_script)
    assert isinstance(result2, dryrun_module._WorkerFailure)
    # the hint must teach the scope rule (this./parent.), the top real-world cause
    hint2 = result2.fix_hint
    assert "this." in hint2 and "parent." in hint2


def test_dm002_scope_hint_matches_native_nested_scope_rules() -> None:
    positive_xml = """<setup rngSeed="1">
        <generate name="outer" count="1" target="JSON">
            <nestedKey name="inner" type="list" count="1">
                <variable name="sibling" constant="sibling_value"/>
                <key name="copied" script="sibling"/>
            </nestedKey>
        </generate>
    </setup>"""
    positive = _execute_source(positive_xml, max_count=2)
    assert positive.ok
    assert positive.captured.products[0].rows[0]["inner"][0]["copied"] == "sibling_value"

    negative_xml = """<setup rngSeed="1">
        <generate name="outer" count="1" target="JSON">
            <nestedKey name="middle" type="list" count="1">
                <variable name="mid" constant="middle_value"/>
                <nestedKey name="leaf" type="list" count="1">
                    <key name="bare_mid_from_leaf" script="mid"/>
                </nestedKey>
            </nestedKey>
        </generate>
    </setup>"""
    negative = _capture_here(negative_xml)
    assert isinstance(negative, dryrun_module._WorkerFailure)
    assert negative.error.code is ErrorCode.TASK_CONFIG
    assert negative.error.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert "expression 'configured expression'" in negative.message
    assert type(negative.error.__cause__) is NameError
    assert negative.error.__cause__.name == "mid"
    assert "NameError" in negative.message
    assert "this.name" in negative.message and "parent.name" in negative.message
    diagnostic = negative
    assert diagnostic.fix_hint == (
        "A script may reference an unavailable name or an unexpected value structure. "
        "Check spelling, definition order, and value shape. Names in the current scope can "
        "resolve bare or via this.name; existing outermost bare names take precedence on "
        "collisions. Use parent.name for the immediate enclosing scope, root.name for an "
        "outermost field, or a qualified scope path to select the intended value. "
        "Intermediate ancestor names are not automatically available bare. CSV columns "
        "arrive as strings (cast: int(parent.col))."
    )


def test_variable_literal_generator_evaluates_in_scripts() -> None:
    # review-181 issue 4 claimed <variable generator="IncrementGenerator"/> parses but
    # never evaluates. It DOES evaluate — the original failure was a bare name inside a
    # nested scope (needs this.). Pin both forms so the correction cannot rot.
    xml = """<setup rngSeed="1">
        <generate name="customers" count="2" target="ConsoleExporter">
            <key name="customer_id" generator="IncrementGenerator"/>
            <generate name="accounts" count="2" target="ConsoleExporter">
                <variable name="acc_seq" generator="IncrementGenerator"/>
                <key name="account_id" script="parent.customer_id * 10 + this.acc_seq"/>
            </generate>
        </generate>
        <generate name="tickets" count="3" target="ConsoleExporter">
            <variable name="seq" generator="IncrementGenerator"/>
            <key name="ticket_id" script="seq * 100"/>
        </generate>
    </setup>"""
    result = _execute_source(xml)
    assert result.ok, [d.message for d in result.diagnostics]
    rows = {p.name: p.rows for p in result.captured.products}
    # nested: variable increments per parent; composed id is globally unique
    assert [r["account_id"] for r in rows["accounts"]] == [11, 12, 21, 22]
    # top-level: bare name resolves directly
    assert [r["ticket_id"] for r in rows["tickets"]] == [100, 200, 300]


def test_engine_scope_error_keeps_native_identifier_and_safe_repair() -> None:
    xml = """<setup rngSeed="1">
        <generate name="parents" count="2" target="ConsoleExporter">
            <key name="pid" generator="IncrementGenerator"/>
            <generate name="children" count="2" target="ConsoleExporter">
                <key name="broken" script="ghost_field * 2"/>
            </generate>
        </generate>
    </setup>"""
    result = _capture_here(xml)
    assert isinstance(result, dryrun_module._WorkerFailure)
    assert result.error.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert type(result.error.__cause__) is NameError
    assert result.error.__cause__.name == "ghost_field"
    assert result.error.location.element_tag == "key"
    assert result.error.location.attribute == "script"
    assert "configured expression" in result.message
    assert "this." in result.message
    assert "this." in result.fix_hint and "parent." in result.fix_hint


def test_smoke_artifact_scope_keeps_caller_resources_contained(tmp_path: Path, monkeypatch) -> None:
    from datamimic_ce.engine.dsl.api import read_resource_bytes, resource_reader_scope
    from datamimic_ce.engine.io.api import smoke_export

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    inside = workspace / "input.txt"
    inside.write_bytes(b"inside")
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"private-outside")
    attempted = []

    def observe(request):
        with pytest.raises(ValueError, match="outside"):
            read_resource_bytes(outside)
        attempted.append(request.exporter_name)
        return smoke_export(request)

    monkeypatch.setattr("datamimic_ce.engine.io.api.smoke_export", observe)
    with resource_reader_scope(AuthoringWorkspaceContext(workspace).read_resource_bytes):
        diagnostics, evidence = dryrun_module._smoke_export(
            {"rows": ({"id": 1}, {"id": 2})},
            {"rows": ("rows", [("FixedWidth", {"columns": "id[2]"})], "|", "\n")},
        )
        assert evidence.failed_exporters == 0, diagnostics
        assert read_resource_bytes(inside) == b"inside"
        with pytest.raises(ValueError, match="outside"):
            read_resource_bytes(outside)
    assert attempted == ["FixedWidth"]
