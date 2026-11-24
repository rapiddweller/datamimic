# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A project function that raises its own exception class shows the author's message in Build (#707)."""

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest

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


def _failure(call: str):
    evidence = CeBoundedExecutor().execute(BoundedExecutionRequest(xml=_XML.format(call=call), max_count=20))
    (diagnostic,) = evidence.diagnostics
    return diagnostic


def test_a_class_the_project_defines_shows_its_message_and_does_not_crash_the_child() -> None:
    diagnostic = _failure("own")
    assert diagnostic.code is AuthoringSystemDiagnosticCode.CHILD_EXECUTION
    assert "Infeasible: budget exhausted" in diagnostic.message
    assert "defines raised this error" in diagnostic.remediation


def test_any_other_exception_keeps_the_type_only_form() -> None:
    diagnostic = _failure("builtin")
    assert diagnostic.message.endswith("ValueError.")
    assert "secret row value" not in diagnostic.model_dump_json()
