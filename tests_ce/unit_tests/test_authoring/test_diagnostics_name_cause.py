# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A failed Build, lint or bounded run names the cause, not only a title or a generic refusal (#692)."""

from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, BoundedExecutionRequest, LintRequest
from datamimic_ce.errors.codes import IssueCode


def _failure(xml: str):
    evidence = CeBoundedExecutor().execute(BoundedExecutionRequest(xml=xml, max_count=20))
    (diagnostic,) = evidence.diagnostics
    assert diagnostic.code is AuthoringSystemDiagnosticCode.CHILD_EXECUTION
    return diagnostic


def _lint(tmp_path: Path, xml: str):
    (tmp_path / PROJECT_ENTRY_PATH).write_text(xml, encoding="utf-8")
    return create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).lint(LintRequest(xml=xml))


def test_unique_values_pool_names_the_key_the_count_and_the_line() -> None:
    diagnostic = _failure(
        """<setup rngSeed="1">
    <generate name="rows" count="20" target="CSV">
        <key name="color" values="('red', 'green', 'blue')" unique="true"/>
    </generate>
</setup>"""
    )
    assert "<key 'color' unique> exhausted: only 3 distinct values" in diagnostic.message
    assert diagnostic.ce_error is not None and diagnostic.ce_error.issue_code is IssueCode.TASK_KEY_UNIQUE_EXHAUSTED
    assert diagnostic.path == ("descriptor", "model.xml", "key", "unique")
    assert diagnostic.location is not None and diagnostic.location.line == 3


def test_unique_values_pool_that_is_large_enough_runs() -> None:
    xml = """<setup rngSeed="1"><generate name="rows" count="3" target="CSV">
        <key name="color" values="('red', 'green', 'blue')" unique="true"/></generate></setup>"""
    assert CeBoundedExecutor().execute(BoundedExecutionRequest(xml=xml, max_count=20)).diagnostics == ()


def test_unique_generator_that_repeats_names_the_key_and_the_distinct_values() -> None:
    diagnostic = _failure(
        """<setup rngSeed="1"><generate name="rows" count="5" target="CSV">
        <key name="flag" generator="BooleanGenerator" unique="true"/></generate></setup>"""
    )
    assert "<key 'flag' unique> exhausted: only 2 distinct values" in diagnostic.message
    assert diagnostic.location is not None and diagnostic.location.attribute == "unique"


def test_int_on_text_names_the_error_type_the_line_and_keeps_text_as_text() -> None:
    diagnostic = _failure(
        """<setup rngSeed="1">
    <generate name="rows" count="2" target="CSV">
        <variable name="branch" values="('B01', 'B02')"/>
        <key name="n" script="int(branch)"/>
    </generate>
</setup>"""
    )
    assert diagnostic.message.endswith("ValueError.")
    assert "B01" not in diagnostic.message and "B01" not in (diagnostic.remediation or "")  # a value is never shown
    assert diagnostic.path == ("descriptor", "model.xml", "key", "script")
    assert diagnostic.location is not None and diagnostic.location.line == 4
    assert "Keep a text key as text" in (diagnostic.remediation or "")
    assert "cast: int(parent.col)" not in (diagnostic.remediation or "")


def test_a_type_error_keeps_the_cast_remediation_that_fits_text_plus_number() -> None:
    diagnostic = _failure(
        """<setup rngSeed="1"><generate name="rows" count="2" target="CSV">
        <variable name="branch" values="('B01', 'B02')"/><key name="n" script="branch + 1"/></generate></setup>"""
    )
    assert "wrong structure" in diagnostic.message
    assert "cast: int(parent.col)" in (diagnostic.remediation or "")


def test_a_failed_name_lookup_keeps_the_scope_remediation() -> None:
    diagnostic = _failure(
        """<setup rngSeed="1"><generate name="rows" count="2" target="CSV">
        <key name="n" script="ghost + 1"/></generate></setup>"""
    )
    assert "NameError: name 'ghost' is not defined" in diagnostic.message
    assert "cast: int(parent.col)" in (diagnostic.remediation or "")


def test_mistyped_element_with_open_and_close_tag_is_named_by_dm101(tmp_path: Path) -> None:
    result = _lint(
        tmp_path,
        """<setup rngSeed="1">
    <generat name="rows" count="2" target="CSV">
        <key name="id" generator="IncrementGenerator"/>
    </generat>
</setup>""",
    )
    first = result.diagnostics[0]
    assert first.code == "DM101"
    assert first.location is not None and (first.location.element, first.location.line) == ("generat", 2)
    assert first.remediation is not None and "Did you mean <generate>?" in first.remediation
    assert [item.code for item in result.diagnostics][-1] == "descriptor"


def test_a_forbidden_dtd_still_reports_the_parser_refusal_only(tmp_path: Path) -> None:
    result = _lint(tmp_path, '<!DOCTYPE setup [<!ENTITY x "y">]><setup rngSeed="1"/>')
    assert [item.code for item in result.diagnostics] == ["descriptor"]


def test_invalid_type_lists_the_valid_types_in_allowed_values_and_remediation(tmp_path: Path) -> None:
    result = _lint(
        tmp_path,
        '<setup rngSeed="1"><generate name="rows" count="2" target="CSV">'
        '<key name="id" type="integer"/></generate></setup>',
    )
    dm105 = next(item for item in result.diagnostics if item.code == "DM105")
    assert dm105.allowed_values == ("binary", "bool", "decimal", "float", "int", "string")
    assert (
        dm105.remediation is not None and "Use one of: binary, bool, decimal, float, int, string." in dm105.remediation
    )
    assert "integer" not in dm105.remediation  # the written value is never repeated


@pytest.mark.parametrize("tag", ["table", "record", "data"])
def test_an_unrelated_element_name_gets_the_known_elements_not_a_wrong_suggestion(tmp_path: Path, tag: str) -> None:
    result = _lint(
        tmp_path,
        f'<setup rngSeed="1"><generate name="rows" count="2"><{tag} name="x"/></generate></setup>',
    )

    first = next(item for item in result.diagnostics if item.code == "DM101")
    assert first.remediation is not None
    assert "Did you mean" not in first.remediation and "Known elements:" in first.remediation
