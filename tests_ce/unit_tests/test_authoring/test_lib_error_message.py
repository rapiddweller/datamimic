# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A project function that raises its own exception class shows the author's message in Build (#707)."""

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.engine.io.failures import normalize_error_cause_for_transport
from datamimic_ce.errors import ExternalFailureCause, IssueCode

_XML = """<setup rngSeed="1">
  <execute type="python">
class Infeasible(Exception):
    pass

def own(n):
    raise Infeasible("budget exhausted")

def builtin(n):
    raise ValueError("secret row value 42")
  </execute>
  <generate name="rows" count="2" target="CSV">
    <key name="id" generator="IncrementGenerator"/>
    <key name="v" script="{call}(id)"/>
  </generate>
</setup>"""


def _failure_from(xml: str):
    evidence = CeBoundedExecutor().execute(BoundedExecutionRequest(xml=xml, max_count=20))
    (diagnostic,) = evidence.diagnostics
    return diagnostic


def _failure(call: str):
    return _failure_from(_XML.format(call=call))


def test_a_class_the_project_defines_shows_its_message_and_does_not_crash_the_child() -> None:
    diagnostic = _failure("own")
    assert diagnostic.code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert "Infeasible: budget exhausted" in diagnostic.message
    assert "provides raised this error" in diagnostic.remediation


def test_any_other_exception_keeps_the_type_only_form() -> None:
    diagnostic = _failure("builtin")
    assert diagnostic.message.endswith("ValueError.")
    assert "secret row value" not in diagnostic.model_dump_json()


def test_a_long_multi_line_message_is_one_bounded_line() -> None:
    xml = _XML.format(call="own").replace('"budget exhausted"', '"line one\\nline two " + "x" * 1000')
    diagnostic = _failure_from(xml)
    assert "\n" not in diagnostic.message
    assert "Infeasible: line one line two" in diagnostic.message
    assert len(diagnostic.message) < 500


def test_an_empty_message_keeps_the_type_only_form() -> None:
    diagnostic = _failure_from(_XML.format(call="own").replace('Infeasible("budget exhausted")', "Infeasible()"))
    assert diagnostic.message.endswith("Infeasible.")


def test_a_cause_that_cannot_be_loaded_becomes_a_passive_fact() -> None:
    class TwoArgs(Exception):
        def __init__(self, first: str, second: str) -> None:
            super().__init__(first)

    error = ValueError("outer")
    error.__cause__ = TwoArgs("a", "b")
    normalize_error_cause_for_transport(error)
    assert isinstance(error.__cause__, ExternalFailureCause)
    plain = ValueError("outer")
    plain.__cause__ = KeyError("k")
    normalize_error_cause_for_transport(plain)
    assert isinstance(plain.__cause__, KeyError)
