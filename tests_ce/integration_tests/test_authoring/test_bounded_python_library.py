# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A Python library loaded by <execute> reaches Ready through Build when it passes the library check (#332)."""

import shutil
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.coverage import CoverageGapKind
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from tests_ce.authoring_project import build_project

_MODELS = Path(__file__).resolve().parents[2] / "fixtures" / "authoring" / "bounded_python_library"


def _build(tmp_path: Path, filename: str):
    """Build ``filename`` as the entry of a copy of the models, so its library paths resolve unchanged."""
    project = shutil.copytree(_MODELS, tmp_path / "project")
    return build_project(project, (_MODELS / filename).read_text(encoding="utf-8"), max_count=5)


def _rows(result) -> list[dict]:
    return [dict(row) for product in result.evidence for row in product.rows]


@pytest.mark.integration
@pytest.mark.parametrize("filename", ["library_inline.xml", "library_unseeded.xml"])
def test_library_function_reaches_ready_without_replay_when_unseeded(tmp_path: Path, filename: str) -> None:
    result = _build(tmp_path, filename)
    assert result.outcome == "ready_with_gaps", result
    assert CoverageGapKind.SEEDED in result.coverage.open_gaps
    assert [row["person_id"] for row in _rows(result)] == [2]
    assert result.verification.deterministic_replay.status is VerificationGateStatus.NOT_REQUESTED


@pytest.mark.integration
def test_seeded_library_loads_once_and_build_replays_it_unrequested(tmp_path: Path) -> None:
    result = _build(tmp_path, "library_seeded.xml")
    assert result.outcome == "ready", result
    rows = _rows(result)
    assert [(row["person_id"], row["loads"]) for row in rows] == [(2, 1), (2, 1)]
    assert rows[0]["draw"] != rows[1]["draw"]
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


@pytest.mark.integration
@pytest.mark.parametrize(
    ("filename", "script", "line", "message"),
    [
        (
            "library_import_in_function.xml",
            "import_in_function.scr.py",
            2,
            "Bounded Python library imports inside a function or class body",
        ),
        (
            "library_reads_file.xml",
            "reads_file.scr.py",
            2,
            "Bounded Python library uses a file or dynamic-code builtin",
        ),
        ("library_indented.xml", "indented_import.scr.py", 1, "Bounded Python library imports a module outside"),
    ],
)
def test_library_check_refuses_before_the_library_runs(
    tmp_path: Path, filename: str, script: str, line: int, message: str
) -> None:
    result = _build(tmp_path, filename)
    assert result.outcome == "rejected"
    [diagnostic] = [
        item
        for item in result.diagnostics
        if item.code is AuthoringRuleId.SIDE_EFFECT and item.message.startswith(message)
    ]
    assert diagnostic.path == ("descriptor", "datamimic.xml")
    assert diagnostic.location is not None
    assert diagnostic.location.script_file == f"lib/{script}"
    assert diagnostic.location.script_line == line


@pytest.mark.integration
def test_library_check_refuses_reserved_string_in_inline_python(tmp_path: Path) -> None:
    result = _build(tmp_path, "library_reserved_name.xml")
    assert result.outcome == "rejected"
    [diagnostic] = [item for item in result.diagnostics if item.code is AuthoringRuleId.SIDE_EFFECT]
    assert "Python library line 1 uses a file or dynamic-code builtin" in diagnostic.message
    assert diagnostic.path == ("descriptor", "datamimic.xml")


def _bounded_run(filename: str):
    workspace = AuthoringWorkspaceContext(_MODELS, PurePosixPath(filename))
    return CeBoundedExecutor(workspace).execute(
        BoundedExecutionRequest(
            xml=(_MODELS / filename).read_text(encoding="utf-8"), descriptor_path=workspace.descriptor_path, max_count=5
        )
    )


@pytest.mark.integration
@pytest.mark.parametrize("filename", ["library_entry.xml", "library_included.xml"])
def test_entry_or_included_step_may_load_a_library(filename: str) -> None:
    result = _bounded_run(filename)
    assert result.ok, result.diagnostics
    assert [dict(row) for product in result.captured.products for row in product.rows] == [{"person_id": 2}]


@pytest.mark.integration
def test_included_library_is_checked_against_the_entry_seed() -> None:
    result = _bounded_run("library_included_refused.xml")
    assert not result.ok
    assert any(
        item.code is AuthoringRuleId.SIDE_EFFECT and item.message.startswith("Bounded Python library imports inside")
        for item in result.diagnostics
    ), result.diagnostics
    [diagnostic] = [item for item in result.diagnostics if item.code is AuthoringRuleId.SIDE_EFFECT]
    assert diagnostic.location is not None
    assert diagnostic.location.script_file == "lib/import_in_function.scr.py"
    assert diagnostic.location.script_line == 2


@pytest.mark.integration
def test_forced_replay_names_why_a_seeded_library_model_failed(tmp_path: Path) -> None:
    result = _build(tmp_path, "library_module_level_draw.xml")
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status is VerificationGateStatus.FAILED
    assert any(item.message.startswith("A seeded model that loads Python must replay") for item in result.diagnostics)


@pytest.mark.integration
@pytest.mark.parametrize("relative", [False, True])
def test_library_outside_the_workspace_is_refused_not_loaded(tmp_path: Path, relative: bool) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (tmp_path / "outside.py").write_text("VALUE = 41\n", encoding="utf-8")
    uri = "../outside.py" if relative else (tmp_path / "outside.py").as_posix()
    (workspace / "step.xml").write_text(
        f'<setup><execute uri="{uri}"/><generate name="rows" count="1" target="">'
        '<key name="v" script="VALUE"/></generate></setup>',
        encoding="utf-8",
    )
    context = AuthoringWorkspaceContext(workspace, PurePosixPath("entry.xml"))
    result = CeBoundedExecutor(context).execute(
        BoundedExecutionRequest(xml='<setup><include uri="step.xml"/></setup>', descriptor_path=context.descriptor_path)
    )
    assert not result.ok
    assert not result.captured.products
    assert any(
        item.message == "Python library uri must name a file inside the workspace" for item in result.diagnostics
    ), result.diagnostics
