# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Dry-run: capped, capture-only execution with the safety gates."""

from pathlib import Path

from datamimic_ce.authoring.dryrun import dry_run_source

_PIPELINE = """<setup rngSeed="1">
    <memstore id="mem"/>
    <generate name="users" count="500" target="mem,CSV,ConsoleExporter">
        <key name="id" generator="IncrementGenerator"/>
        <key name="age" type="int" min="18" max="99"/>
    </generate>
    <generate name="from_mem" source="mem" type="users" distribution="ordered" target="JSON"/>
</setup>"""


def test_dry_run_caps_counts_strips_targets_keeps_memstore(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)  # any accidental artifact would land here
    result = dry_run_source(_PIPELINE, max_count=7, sample_rows=3)
    assert result.ok and result.stage == "run", [d.message for d in result.diagnostics]

    by_name = {p.name: p for p in result.products}
    assert by_name["users"].count == 7  # capped from 500
    assert by_name["from_mem"].count == 7  # memstore target kept -> pipeline works
    assert len(by_name["users"].sample) == 3 and by_name["users"].truncated_rows
    assert by_name["users"].sample[0]["id"] == 1

    # no artifacts anywhere: CSV/JSON/Console were stripped
    assert not list(tmp_path.rglob("*.csv")) and not list(tmp_path.rglob("output"))


def test_dry_run_lint_gate_blocks_broken_descriptor() -> None:
    result = dry_run_source("<setup><generate name='a' pagesize='5' target='ConsoleExporter'/></setup>")
    assert not result.ok and result.stage == "lint"
    assert any(d.rule == "DM103" for d in result.diagnostics)


def test_dry_run_refuses_execute_without_allow() -> None:
    xml = """<setup rngSeed="1">
        <execute uri="script/x.sql"/>
        <generate name="a" count="1" target="ConsoleExporter"><key name="x" constant="1"/></generate>
    </setup>"""
    result = dry_run_source(xml)
    assert not result.ok and result.stage == "run"
    assert [d.rule for d in result.diagnostics] == ["DM003"]


def test_dry_run_maps_runtime_error_to_dm002() -> None:
    # lints clean (source file simply missing at runtime) -> DM002 with hint
    xml = """<setup rngSeed="1">
        <generate name="a" count="3" source="missing.csv" distribution="ordered" target="ConsoleExporter"/>
    </setup>"""
    result = dry_run_source(xml)
    assert not result.ok and result.stage == "run"
    assert [d.rule for d in result.diagnostics] == ["DM002"]
    assert result.diagnostics[0].fix_hint
