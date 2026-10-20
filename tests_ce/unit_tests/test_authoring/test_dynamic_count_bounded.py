# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Bounded Authoring evaluates dynamic counts at runtime instead of replacing them.

Replacing count="{int(headcount)}" with max_count made the capture "capped" forever and
never evaluated the expression, so dry-run said ok while `datamimic run` crashed on a
wrong scope. The bounded rows must equal the real run's rows."""

import json
import shutil
from collections import Counter
from pathlib import Path, PurePosixPath

from typer.testing import CliRunner

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.engine.runtime.api import create_run_session
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.errors import GUIDANCE_COUNT_SCOPE
from datamimic_ce.errors.codes import IssueCode
from datamimic_ce.interfaces.cli import app

_FIXTURES = Path(__file__).parent / "fixtures"
_DEPARTMENTS = "fx_dynamic_child_count.departments.csv"


def _bounded(fixture: str):
    path = _FIXTURES / fixture
    logical = PurePosixPath(path.name)
    return CeBoundedExecutor(AuthoringWorkspaceContext(path.parent, logical)).execute(
        BoundedExecutionRequest(xml=path.read_text(encoding="utf-8"), descriptor_path=logical)
    )


def test_dynamic_child_count_is_evaluated_and_matches_the_real_run(tmp_path: Path) -> None:
    result = _bounded("fx_dynamic_child_count.xml")
    assert result.ok, result.diagnostics
    employees = {product.name: product for product in result.captured.products}["employees"]
    assert employees.capture.status.value == "complete"
    assert Counter(row["dept_id"] for row in employees.rows) == {"10": 4, "20": 3, "30": 2, "40": 3}

    for name in ("fx_dynamic_child_count.xml", _DEPARTMENTS):
        shutil.copy(_FIXTURES / name, tmp_path / name)
    session = create_run_session(RunRequest(descriptor_path=tmp_path / "fx_dynamic_child_count.xml", test_mode=True))
    session.execute()
    assert session.capture_test_result()["employees"] == list(employees.rows)


def test_dynamic_child_count_builds_ready_with_replay(tmp_path: Path) -> None:
    runner = CliRunner()
    shutil.copy(_FIXTURES / _DEPARTMENTS, tmp_path / _DEPARTMENTS)
    decompiled = runner.invoke(app, ["authoring", "decompile", str(_FIXTURES / "fx_dynamic_child_count.xml")])
    build = tmp_path / "build.json"
    build.write_text(
        json.dumps(
            {
                "document": json.loads(decompiled.output)["document"],
                "expectations": [
                    {"kind": "exact_count", "subject": {"kind": "product", "product": "employees"}, "count": 12},
                    {"kind": "unique", "subject": {"kind": "product", "product": "employees"}, "field": "employee_id"},
                ],
                "verification": {"deterministic_replay": True},
            }
        ),
        encoding="utf-8",
    )
    result = runner.invoke(app, ["authoring", "build", str(build)])
    payload = json.loads(result.output)
    assert payload["outcome"] == "ready", payload["diagnostics"]
    assert payload["verification"]["deterministic_replay"]["status"] == "passed"


def test_parent_scoped_count_fails_in_bounded_execution_with_count_guidance() -> None:
    result = _bounded("fx_dynamic_child_count_parent_scope.xml")
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.path[-2:] == ("generate", "count")
    assert diagnostic.remediation == GUIDANCE_COUNT_SCOPE


def test_non_integer_count_failure_still_names_the_count_attribute() -> None:
    result = _bounded("fx_dynamic_child_count_non_integer.xml")
    assert not result.ok
    assert result.diagnostics[0].path[-2:] == ("generate", "count")


def test_count_above_bounded_limit_is_refused_not_truncated() -> None:
    result = _bounded("fx_dynamic_child_count_above_limit.xml")
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.ce_error is not None
    assert diagnostic.ce_error.issue_code is IssueCode.TASK_COUNT_ABOVE_BOUNDED_LIMIT
    assert diagnostic.path[-2:] == ("generate", "count")
