# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Dry-run: capped, capture-only execution with the safety gates."""

import json
from multiprocessing.connection import Connection
from pathlib import Path

import pytest

import datamimic_ce.authoring.dryrun as dryrun_module
from datamimic_ce.authoring.contracts import (
    AuthoringStage,
    ScaffoldRequest,
    ScaffoldVerification,
    VerificationGateStatus,
)
from datamimic_ce.authoring.dryrun import dry_run_source, dry_run_source_captured
from datamimic_ce.authoring.service import compile_document, scaffold
from datamimic_ce.exporters.json_exporter import JsonExporter

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


def _short_write_worker(
    path: Path,
    max_count: int,
    allow_side_effects: bool,
    smoke_export: bool,
    send_connection: Connection,
) -> None:
    JsonExporter._write_data_to_buffer = _short_write_json
    dryrun_module._engine_process_worker(path, max_count, allow_side_effects, smoke_export, send_connection)


def test_dry_run_caps_counts_strips_targets_keeps_memstore(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)  # any accidental artifact would land here
    result = dry_run_source(_PIPELINE, max_count=7, sample_rows=3)
    assert result.ok and result.stage is AuthoringStage.RUN, [d.message for d in result.diagnostics]

    by_name = {p.name: p for p in result.products}
    assert by_name["users"].count == 7  # capped from 500
    assert by_name["from_mem"].count == 7  # memstore target kept -> pipeline works
    assert len(by_name["users"].sample) == 3 and by_name["users"].truncated_rows
    assert by_name["users"].sample[0]["id"] == 1

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
    result = dry_run_source(xml, max_count=5, sample_rows=2)
    assert result.ok, [d.message for d in result.diagnostics]
    row = result.products[0].sample[0]
    assert isinstance(row["reviews"], list) and len(row["reviews"]) == 2
    assert isinstance(row["reviews"][0], dict) and 1 <= row["reviews"][0]["rating"] <= 5


def test_dry_run_lint_gate_blocks_broken_descriptor() -> None:
    result = dry_run_source("<setup><generate name='a' pagesize='5' target='ConsoleExporter'/></setup>")
    assert not result.ok and result.stage is AuthoringStage.LINT
    assert any(d.rule == "DM103" for d in result.diagnostics)


def test_dry_run_refuses_execute_without_allow() -> None:
    xml = """<setup rngSeed="1">
        <execute uri="script/x.sql"/>
        <generate name="a" count="1" target="ConsoleExporter"><key name="x" constant="1"/></generate>
    </setup>"""
    result = dry_run_source(xml)
    assert not result.ok and result.stage is AuthoringStage.RUN
    assert [d.rule for d in result.diagnostics] == ["DM003"]


def test_dry_run_maps_runtime_error_to_dm002() -> None:
    # lints clean (source file simply missing at runtime) -> DM002 with hint
    xml = """<setup rngSeed="1">
        <generate name="a" count="3" source="missing.csv" distribution="ordered" target="ConsoleExporter"/>
    </setup>"""
    result = dry_run_source(xml)
    assert not result.ok and result.stage is AuthoringStage.RUN
    assert [d.rule for d in result.diagnostics] == ["DM002"]
    assert result.diagnostics[0].fix_hint


def test_dm004_flags_zero_row_output() -> None:
    # An empty/mis-wired descriptor runs clean but generates nothing — surface it.
    empty = dry_run_source("<setup></setup>")
    assert not empty.ok  # no crash, but no useful output either
    assert [d.rule for d in empty.diagnostics] == ["DM004"]
    assert empty.diagnostics[0].severity.value == "warning"

    # a real descriptor that produces rows must NOT get DM004
    real = dry_run_source(
        '<setup rngSeed="1"><generate name="g" count="3" target="JSON">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>'
    )
    assert real.ok and real.products[0].count == 3
    assert not [d for d in real.diagnostics if d.rule == "DM004"]


def test_smoke_export_passes_and_leaves_no_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run = dry_run_source_captured(_SMOKE_EXPORT_MATRIX.read_text(encoding="utf-8"), smoke_export=True)
    assert run.result.ok, [(d.rule, d.message) for d in run.result.diagnostics]
    assert {product.name: product.count for product in run.result.products} == {"audit": 2, "items": 4}
    assert run.smoke_export.applicable_exporters == 9
    assert run.smoke_export.attempted_exporters == 9
    assert run.smoke_export.failed_exporters == 0
    assert not list(tmp_path.iterdir())  # smoke writes never leave the temp dir


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
    result = dry_run_source((_FIXTURES / fixture).read_text(encoding="utf-8"), smoke_export=True)
    assert result.ok, [(diagnostic.rule, diagnostic.message) for diagnostic in result.diagnostics]
    assert result.products[0].count == expected_rows
    assert not list(tmp_path.iterdir())


def test_smoke_export_honors_target_encoding(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = dry_run_source(
        (_FIXTURES / "issue_227_smoke_export_ascii_encoding.xml").read_text(encoding="utf-8"),
        smoke_export=True,
    )
    assert not result.ok
    assert any(diagnostic.rule == "DM002" for diagnostic in result.diagnostics)
    assert not list(tmp_path.iterdir())


def test_issue_256_fixed_width_smoke_export_reads_rows_with_target_encoding(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = dry_run_source_captured(
        (_FIXTURES / "issue_256_fixed_width_latin1.xml").read_text(encoding="utf-8"),
        smoke_export=True,
    )

    assert result.result.ok, [(d.rule, d.message) for d in result.result.diagnostics]
    assert result.result.stage is AuthoringStage.RUN
    assert {product.name: product.count for product in result.result.products} == {"rows": 3}
    assert result.smoke_export.applicable_exporters == 1
    assert result.smoke_export.attempted_exporters == 1
    assert result.smoke_export.failed_exporters == 0
    assert not list(tmp_path.iterdir())


def test_issue_256_ndjson_chunk_one_smoke_export_counts_each_row_once(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = dry_run_source_captured(
        (_FIXTURES / "issue_256_json_ndjson_chunk_one.xml").read_text(encoding="utf-8"),
        smoke_export=True,
    )

    assert result.result.ok, [(d.rule, d.message) for d in result.result.diagnostics]
    assert result.result.stage is AuthoringStage.RUN
    assert {product.name: product.count for product in result.result.products} == {"rows": 3}
    assert result.smoke_export.applicable_exporters == 1
    assert result.smoke_export.attempted_exporters == 1
    assert result.smoke_export.failed_exporters == 0
    assert not list(tmp_path.iterdir())


def test_smoke_export_catches_unserializable_value_plain_dry_run_does_not(tmp_path: Path, monkeypatch) -> None:
    # THE asymmetry that motivates the feature: a value only the export layer rejects.
    # The bad product is NESTED on purpose — nested products must be smoked too
    # (their capture key differs from the statement full_name).
    monkeypatch.chdir(tmp_path)
    xml = """<setup rngSeed="1">
        <generate name="batches" count="2" target="ConsoleExporter">
            <key name="batch_id" generator="IncrementGenerator"/>
            <generate name="blobs" count="2" target="JSON">
                <key name="payload" script="re.compile('exotic')"/>
            </generate>
        </generate>
    </setup>"""
    plain = dry_run_source(xml)
    assert plain.ok  # the gap: JSON target stripped, crash invisible

    smoked = dry_run_source(xml, smoke_export=True)
    assert not smoked.ok and smoked.stage is AuthoringStage.RUN
    diag = next(d for d in smoked.diagnostics if d.rule == "DM002")
    assert "JSON" in diag.message and "serializable" in diag.message
    assert diag.name == "batches|blobs"  # names the offending (nested) product
    assert "JSON" in diag.fix_hint
    assert not list(tmp_path.iterdir())  # even the failing run leaves nothing behind


def test_smoke_export_compares_buffered_exporter_row_count(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    model = json.loads((_FIXTURES / "issue_227_smoke_rows.model.dm.json").read_text(encoding="utf-8"))
    xml = (_FIXTURES / "issue_227_smoke_rows.xml").read_text(encoding="utf-8").strip()
    assert compile_document(model).xml == xml
    request = ScaffoldRequest(
        spec=model,
        max_count=10,
        sample_rows=5,
        verification=ScaffoldVerification(smoke_export=True),
    )
    positive = scaffold(request)
    assert positive.xml == xml
    assert positive.verified
    assert positive.verification.smoke_export.status is VerificationGateStatus.PASSED
    assert positive.verification.smoke_export.reason == "Every applicable file exporter wrote all captured rows"

    monkeypatch.setattr(dryrun_module, "_engine_process_worker", _short_write_worker)
    monkeypatch.setattr(JsonExporter, "_write_data_to_buffer", _short_write_json)
    negative = scaffold(request)

    assert not negative.ok
    assert not negative.verified
    assert negative.verification.smoke_export.status is VerificationGateStatus.FAILED
    assert negative.verification.smoke_export.failed_exporters == 1
    diagnostic = next(d for d in negative.diagnostics if d.rule == "DM002")
    assert "wrote 2 of 3 captured rows" in diagnostic.message
    assert not list(tmp_path.iterdir())


def test_dm002_runtime_errors_carry_actionable_hints() -> None:
    """Runtime crashes must teach the fix, not just echo the traceback — the loop
    depends on it. Each signature maps to a specific hint, not the generic fallback."""
    empty_memstore = """<setup rngSeed="1"><memstore id="mem"/>
        <iterate name="r" source="mem" type="nope" distribution="ordered" count="3" target="ConsoleExporter"/>
    </setup>"""
    result = dry_run_source(empty_memstore)
    assert not result.ok
    hint = result.diagnostics[0].fix_hint
    assert "memstore" in hint.lower() and "before" in hint.lower()
    assert "Fix the reported runtime error" not in hint  # not the generic fallback

    bad_script = """<setup rngSeed="1">
        <generate name="o" count="3" target="ConsoleExporter"><key name="x" script="ghost * 3"/></generate>
    </setup>"""
    result2 = dry_run_source(bad_script)
    assert not result2.ok
    # the hint must teach the scope rule (this./parent.), the top real-world cause
    hint2 = result2.diagnostics[0].fix_hint
    assert "this." in hint2 and "parent." in hint2


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
    result = dry_run_source(xml)
    assert result.ok, [d.message for d in result.diagnostics]
    rows = {p.name: p.sample for p in result.products}
    # nested: variable increments per parent; composed id is globally unique
    assert [r["account_id"] for r in rows["accounts"]] == [11, 12, 21, 22]
    # top-level: bare name resolves directly
    assert [r["ticket_id"] for r in rows["tickets"]] == [100, 200, 300]


def test_engine_scope_error_names_the_missing_identifier() -> None:
    # The engine message itself (not just the hint) must say WHICH name is missing —
    # "have undefined item or wrong structure" hid it (review-181 issue 2).
    xml = """<setup rngSeed="1">
        <generate name="parents" count="2" target="ConsoleExporter">
            <key name="pid" generator="IncrementGenerator"/>
            <generate name="children" count="2" target="ConsoleExporter">
                <key name="broken" script="ghost_field * 2"/>
            </generate>
        </generate>
    </setup>"""
    result = dry_run_source(xml)
    assert not result.ok and result.stage is AuthoringStage.RUN
    diag = next(d for d in result.diagnostics if d.rule == "DM002")
    assert "ghost_field" in diag.message  # the identifier, verbatim
    assert "this." in diag.message  # and the scope guidance travels with it
    assert "this." in diag.fix_hint and "parent." in diag.fix_hint
