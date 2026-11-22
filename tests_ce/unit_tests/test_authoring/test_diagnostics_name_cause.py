# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A failed Build, lint or bounded run names the cause, not only a title or a generic refusal (#692)."""

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.errors.codes import IssueCode


def _failure(xml: str):
    evidence = CeBoundedExecutor().execute(BoundedExecutionRequest(xml=xml, max_count=20))
    (diagnostic,) = evidence.diagnostics
    assert diagnostic.code is AuthoringSystemDiagnosticCode.CHILD_EXECUTION
    return diagnostic


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
