# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A target named by a .properties include resolves the way the runtime resolves it (#366)."""

from pathlib import Path

from tests_ce.authoring_project import build_project

_COUNT = {"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 2}
_STEP = '<setup><generate name="rows" count="2" target="{sink}"><key name="x" constant="1"/></generate></setup>'


def _entry(*, sink: str | None) -> str:
    return (
        '<setup rngSeed="1"><include uri="conf/base.properties"/><include uri="delivery/90_export.xml"/></setup>'
        if sink is not None
        else '<setup rngSeed="1"><include uri="delivery/90_export.xml"/></setup>'
    )


def _project(root: Path, sink: str | None) -> Path:
    (root / "conf").mkdir()
    (root / "delivery").mkdir()
    (root / "conf" / "base.properties").write_text("sink=CSV\n", encoding="utf-8")
    (root / "delivery" / "90_export.xml").write_text(_STEP, encoding="utf-8")
    return root


def test_a_step_target_from_conf_properties_reaches_ready(tmp_path: Path) -> None:
    root = _project(tmp_path, "CSV")
    result = build_project(root, _entry(sink="CSV"), version="5.0", expectations=[_COUNT])
    assert result.outcome == "ready", result.diagnostics


def test_an_undefined_placeholder_is_still_rejected_at_the_step_element(tmp_path: Path) -> None:
    root = _project(tmp_path, None)
    result = build_project(root, _entry(sink=None), version="5.0", expectations=[_COUNT])
    assert result.outcome == "rejected"
    assert [item.path for item in result.diagnostics if item.code == "DM401"] == [
        ("include", "delivery/90_export.xml", "/setup/generate", "line", 1)
    ], result.diagnostics


def test_a_property_naming_an_undeclared_target_is_rejected_without_echoing_its_value(tmp_path: Path) -> None:
    root = _project(tmp_path, "CSV")
    (root / "conf" / "base.properties").write_text("sink=secret_sink_name\n", encoding="utf-8")
    result = build_project(root, _entry(sink="x"), version="5.0", expectations=[_COUNT])
    assert result.outcome == "rejected"
    assert any(item.code == "DM401" for item in result.diagnostics), result.diagnostics
    assert "secret_sink_name" not in result.model_dump_json()


def _ordered_project(root: Path, entry: str, step: str | None = None) -> Path:
    (root / "conf").mkdir()
    (root / "delivery").mkdir()
    (root / "conf" / "base.properties").write_text("sink=CSV\n", encoding="utf-8")
    if step is not None:
        (root / "delivery" / "90_export.xml").write_text(step, encoding="utf-8")
    return root


def test_a_properties_include_after_the_step_does_not_resolve_the_step(tmp_path: Path) -> None:
    # The runtime parses the step before it reads the properties, so it fails there; Build must not say ready.
    root = _ordered_project(tmp_path, "", _STEP)
    entry = '<setup rngSeed="1"><include uri="delivery/90_export.xml"/><include uri="conf/base.properties"/></setup>'
    result = build_project(root, entry, version="5.0", expectations=[_COUNT])
    assert result.outcome == "rejected"
    assert any(item.code == "DM401" for item in result.diagnostics), result.diagnostics


def test_a_generate_before_the_properties_include_is_not_resolved(tmp_path: Path) -> None:
    root = _ordered_project(tmp_path, "")
    entry = (
        '<setup rngSeed="1"><generate name="rows" count="2" target="{sink}"><key name="x" constant="1"/></generate>'
        '<include uri="conf/base.properties"/></setup>'
    )
    result = build_project(root, entry, version="5.0", expectations=[_COUNT])
    assert result.outcome == "rejected"
    assert any(item.code == "DM401" for item in result.diagnostics), result.diagnostics


def test_a_generate_after_the_properties_include_is_resolved(tmp_path: Path) -> None:
    root = _ordered_project(tmp_path, "")
    entry = (
        '<setup rngSeed="1"><include uri="conf/base.properties"/>'
        '<generate name="rows" count="2" target="{sink}"><key name="x" constant="1"/></generate></setup>'
    )
    result = build_project(root, entry, version="5.0", expectations=[_COUNT])
    assert result.outcome == "ready", result.diagnostics
