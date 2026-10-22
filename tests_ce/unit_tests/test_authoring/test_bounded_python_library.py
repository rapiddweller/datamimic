# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A Python library loaded by <execute> reaches Ready through Build when it passes the library check (#332)."""

import shutil
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.authoring.domain.script_semantics import LibraryRefusalReason as Reason
from datamimic_ce.authoring.domain.script_semantics import python_library_refusal
from datamimic_ce.engine.dsl.vocabulary.contracts.dsl_element import BoundedExecutionStrategy
from tests_ce.authoring_project import build_project

_MODELS = Path(__file__).parent / "bounded_python_library"


def _build(tmp_path: Path, filename: str):
    """Build ``filename`` as the entry of a copy of the models, so its library paths resolve unchanged."""
    project = shutil.copytree(_MODELS, tmp_path / "project")
    return build_project(project, (_MODELS / filename).read_text(encoding="utf-8"), max_count=5)


def _rows(result) -> list[dict]:
    return [dict(row) for product in result.evidence for row in product.rows]


@pytest.mark.parametrize("filename", ["library_inline.xml", "library_unseeded.xml"])
def test_library_function_reaches_ready_without_replay_when_unseeded(tmp_path: Path, filename: str) -> None:
    result = _build(tmp_path, filename)
    assert result.outcome == "ready", result
    assert [row["person_id"] for row in _rows(result)] == [2]
    assert result.verification.deterministic_replay.status is VerificationGateStatus.NOT_REQUESTED


def test_seeded_library_loads_once_and_build_replays_it_unrequested(tmp_path: Path) -> None:
    result = _build(tmp_path, "library_seeded.xml")
    assert result.outcome == "ready", result
    rows = _rows(result)
    assert [(row["person_id"], row["loads"]) for row in rows] == [(2, 1), (2, 1)]
    assert rows[0]["draw"] != rows[1]["draw"]
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


@pytest.mark.parametrize(
    ("filename", "message"),
    [
        (
            "library_import_in_function.xml",
            "import_in_function.scr.py: Python library line 2 imports inside a function or class body",
        ),
        ("library_reads_file.xml", "reads_file.scr.py: Python library line 2 uses a file or dynamic-code builtin"),
        ("library_indented.xml", "indented_import.scr.py: Python library line 1 imports a module outside"),
    ],
)
def test_library_check_refuses_before_the_library_runs(tmp_path: Path, filename: str, message: str) -> None:
    result = _build(tmp_path, filename)
    assert result.outcome == "rejected"
    assert any(
        item.code is AuthoringRuleId.SIDE_EFFECT and item.message.startswith(message) for item in result.diagnostics
    ), result.diagnostics


@pytest.mark.parametrize("filename", ["execute_sql.xml", "execute_per_row.xml"])
def test_execute_outside_a_setup_level_python_library_is_refused_by_policy(tmp_path: Path, filename: str) -> None:
    result = _build(tmp_path, filename)
    assert result.outcome == "rejected"
    assert [item.code for item in result.diagnostics] == [AuthoringRuleId.UNSUPPORTED_BOUNDED_OPERATION]


@pytest.mark.parametrize(
    ("source", "seeded", "reason"),
    [
        ("import random\nLOADS = [random.random]\n", True, None),
        ("from datamimic_ce.domains.api import BaseLiteralGenerator\n", False, None),
        ("def f():\n    import random\n", False, None),
        ("def f():\n    import random\n", True, Reason.IMPORT_INSIDE_BODY_UNDER_SEED),
        ("class G:\n    def f(self):\n        from uuid import uuid4\n", True, Reason.IMPORT_INSIDE_BODY_UNDER_SEED),
        ("import subprocess\n", False, Reason.IMPORT_NOT_ADMITTED),
        ("from datamimic_ce.engine.io.api import database_count_table_length\n", False, Reason.IMPORT_NOT_ADMITTED),
        ("from . import sibling\n", False, Reason.IMPORT_NOT_ADMITTED),
        ("VALUE = eval('1')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("write = open\nwrite('/x', 'w')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("load = __import__\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("x = __builtins__['open']\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f():\n    return globals()\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f():\n    return f.__globals__\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f():\n    return getattr(f, '__globals__')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("g = getattr\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f():\n    return print.__self__.open('/x', 'w')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("def f(module):\n    return module.__import__('subprocess')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        (
            "def f():\n    return object.__getattribute__(f, '__glo' + 'bals__')\n",
            False,
            Reason.FILE_OR_DYNAMIC_CODE_BUILTIN,
        ),
        ("def f(o, n):\n    return getattr(o, '__' + n)\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("import random\nDATA = random.__loader__\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("from re import compile\nPATTERN = compile('a+')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("from re import compile as open\ndel open\nopen('/x')\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        ("import re\nPATTERN = re.compile('a+')\n", False, None),
        ("import random\nB = random.__dict__['__builtins__']\n", False, Reason.FILE_OR_DYNAMIC_CODE_BUILTIN),
        (
            "import random\nB = getattr(random, '__dict__')['__builtins__']\n",
            False,
            Reason.FILE_OR_DYNAMIC_CODE_BUILTIN,
        ),
        ("class Row:\n    def as_dict(self):\n        return dict(self.__dict__)\n", False, None),
        ("def broken(:\n", False, None),
    ],
)
def test_python_library_refusal(source: str, seeded: bool, reason: Reason | None) -> None:
    refusal = python_library_refusal(source, seeded=seeded)
    assert (refusal.reason if refusal else None) is reason


def test_refusal_names_the_earliest_line_and_no_source_text() -> None:
    refusal = python_library_refusal("SECRET = 'token-123'\nimport socket\nx = open('a')\n", seeded=False)
    assert refusal is not None and refusal.line == 2
    assert "token-123" not in refusal.message() and "socket" not in refusal.message()


def _bounded_run(filename: str):
    workspace = AuthoringWorkspaceContext(_MODELS, PurePosixPath(filename))
    return CeBoundedExecutor(workspace).execute(
        BoundedExecutionRequest(
            xml=(_MODELS / filename).read_text(encoding="utf-8"), descriptor_path=workspace.descriptor_path, max_count=5
        )
    )


@pytest.mark.parametrize("filename", ["library_entry.xml", "library_included.xml"])
def test_entry_or_included_step_may_load_a_library(filename: str) -> None:
    result = _bounded_run(filename)
    assert result.ok, result.diagnostics
    assert [dict(row) for product in result.captured.products for row in product.rows] == [{"person_id": 2}]


def test_included_library_is_checked_against_the_entry_seed() -> None:
    result = _bounded_run("library_included_refused.xml")
    assert not result.ok
    assert any(
        item.code is AuthoringRuleId.SIDE_EFFECT
        and item.message.startswith("import_in_function.scr.py: Python library line 2 imports inside")
        for item in result.diagnostics
    ), result.diagnostics


def test_forced_replay_names_why_a_seeded_library_model_failed(tmp_path: Path) -> None:
    result = _build(tmp_path, "library_module_level_draw.xml")
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status is VerificationGateStatus.FAILED
    assert any(item.message.startswith("A seeded model that loads Python must replay") for item in result.diagnostics)


def test_published_execute_capability_names_the_library_strategy() -> None:
    capability = create_authoring_application(_MODELS).capability(CapabilityDomain.ELEMENT, "execute").capability
    assert capability.bounded_execution.strategy is BoundedExecutionStrategy.PYTHON_LIBRARY


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
