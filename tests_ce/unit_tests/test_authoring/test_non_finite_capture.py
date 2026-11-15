# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A non-finite number in a captured row is refused with a catalog code and a message without the value."""

from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.capture import validate_capture_values
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.errors import IssueCode, TaskConfigError

_MODEL = (
    '<setup rngSeed="1"><generate name="rows" source="data/scores.json" distribution="ordered">'
    '<key name="id" script="this.id"/><key name="score" script="this.score"/></generate></setup>'
)


def _run(root: Path, source: str):
    (root / "data").mkdir(exist_ok=True)
    (root / "data" / "scores.json").write_text(source, encoding="utf-8")
    workspace = AuthoringWorkspaceContext(root, PurePosixPath("model.xml"))
    return CeBoundedExecutor(workspace).execute(
        BoundedExecutionRequest(xml=_MODEL, descriptor_path=workspace.descriptor_path, max_count=3)
    )


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e309"])
def test_a_non_finite_number_in_a_captured_row_has_a_catalog_code(tmp_path: Path, number: str) -> None:
    result = _run(tmp_path, f'[{{"id": 1, "score": {number}}}]')

    assert not result.ok
    (diagnostic,) = result.diagnostics
    assert diagnostic.ce_error is not None
    assert diagnostic.ce_error.issue_code is IssueCode.TASK_CAPTURE_VALUE_NOT_FINITE
    assert not any(text in diagnostic.message.lower() for text in ("nan", "inf", "1e309"))


def test_a_finite_number_is_captured(tmp_path: Path) -> None:
    assert _run(tmp_path, '[{"id": 1, "score": 2.5}]').ok


def test_the_capture_check_raises_the_catalog_error() -> None:
    with pytest.raises(TaskConfigError) as caught:
        validate_capture_values({"rows": [{"score": float("nan")}]})
    assert caught.value.issue_code is IssueCode.TASK_CAPTURE_VALUE_NOT_FINITE
