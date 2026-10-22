# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The rejections blind agents hit most name the concrete fix, not the generic input remediation (#356 d)."""

from pathlib import Path

from datamimic_ce.authoring.domain.build_rules import authoring_rule_catalog
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from tests_ce.authoring_project import build_project

_GENERIC = next(rule.remediation for rule in authoring_rule_catalog() if rule.rule_id is AuthoringRuleId.INPUT)
_HANDOFF = (
    '<setup rngSeed="1"><memstore id="store"/>'
    '<generate name="parents" count="2" target="store"><key name="id" generator="IncrementGenerator"/></generate>'
    '<generate name="readback" source="store" type="parents" distribution="ordered">'
    '<key name="id" script="this.id"/></generate></setup>'
)


def _first_error(result):
    return next(item for item in result.diagnostics if item.severity == "error")


def test_a_memstore_handoff_without_roles_names_the_role_pair(tmp_path: Path) -> None:
    diagnostic = _first_error(build_project(tmp_path, _HANDOFF))
    assert diagnostic.remediation != _GENERIC
    assert "identifier" in diagnostic.remediation and "foreign_key" in diagnostic.remediation


def test_a_memstore_target_nobody_reads_names_the_readback(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><memstore id="store"/>'
        '<generate name="parents" count="2" target="store"><key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>"
    )
    diagnostic = _first_error(build_project(tmp_path, xml))
    assert diagnostic.remediation != _GENERIC
    assert "source=<memstore id>" in diagnostic.remediation


def test_an_undeclared_expectation_field_names_the_missing_key(tmp_path: Path) -> None:
    xml = '<setup rngSeed="1"><generate name="rows" count="2"><key name="id" constant="1"/></generate></setup>'
    expectation = {"kind": "unique", "subject": {"kind": "product", "product": "rows"}, "field": "code"}
    diagnostic = _first_error(build_project(tmp_path, xml, expectations=[expectation]))
    assert diagnostic.remediation != _GENERIC
    assert "<key>" in diagnostic.remediation


def test_unknown_cardinality_names_the_count_fix(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><variable name="rows" script="[{\'id\': 1}, {\'id\': 2}]"/>'
        '<generate name="rows_out" script="rows"><key name="id" script="id"/></generate></setup>'
    )
    result = build_project(tmp_path, xml)
    messages = [item.message for item in result.diagnostics if item.severity == "error"]
    assert any("literal count" in message for message in messages), result.diagnostics
