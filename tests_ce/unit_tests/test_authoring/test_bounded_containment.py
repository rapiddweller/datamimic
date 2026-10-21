# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A bounded run writes only inside its private directory and starts no process (#361)."""

from pathlib import Path, PurePosixPath

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest


def _run(root: Path, script: str, *, allow_side_effects: bool = False):
    workspace = AuthoringWorkspaceContext(root, PurePosixPath("model.xml"))
    xml = f'<setup><generate name="rows" count="1" target=""><key name="value" script="{script}"/></generate></setup>'
    return CeBoundedExecutor(workspace).execute(
        BoundedExecutionRequest(
            xml=xml, descriptor_path=workspace.descriptor_path, allow_side_effects=allow_side_effects
        )
    )


def test_expression_cannot_write_outside_the_private_workspace(tmp_path: Path) -> None:
    (tmp_path / "workspace").mkdir()
    outside = tmp_path / "outside.csv"
    result = _run(tmp_path / "workspace", f"pd.DataFrame([{{'a': 1}}]).to_csv('{outside.as_posix()}')")
    assert not result.ok
    assert not outside.exists()
    assert any(
        "writes only new files inside its private workspace" in (item.remediation or "") for item in result.diagnostics
    )


def test_expression_cannot_start_a_process(tmp_path: Path) -> None:
    marker = tmp_path / "started"
    result = _run(tmp_path, f"os.system('touch {marker.as_posix()}')")
    assert not result.ok
    assert not marker.exists()
    assert any("starts no process" in (item.remediation or "") for item in result.diagnostics)


def test_writes_inside_the_private_workspace_stay_allowed(tmp_path: Path) -> None:
    result = _run(tmp_path, "pd.DataFrame([{'a': 1}]).to_csv('inside.csv') or 1")
    assert result.ok, result.diagnostics
    assert not (tmp_path / "inside.csv").exists(), "the private copy, not the workspace, received the write"


def test_side_effect_runs_are_not_contained(tmp_path: Path) -> None:
    (tmp_path / "workspace").mkdir()
    outside = tmp_path / "outside.csv"
    result = _run(
        tmp_path / "workspace",
        f"pd.DataFrame([{{'a': 1}}]).to_csv('{outside.as_posix()}') or 1",
        allow_side_effects=True,
    )
    assert result.ok, result.diagnostics
    assert outside.exists()


def test_a_library_cannot_replace_a_later_checked_library(tmp_path: Path) -> None:
    # Codex on #360: the first library rewrites the second after both passed the library check.
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "first.scr.py").write_text(
        "import pandas as pd\n"
        "pd.DataFrame({'x': ['import subprocess']}).to_csv('lib/second.scr.py', index=False, header=False)\n",
        encoding="utf-8",
    )
    (tmp_path / "lib" / "second.scr.py").write_text("VALUE = 1\n", encoding="utf-8")
    workspace = AuthoringWorkspaceContext(tmp_path, PurePosixPath("model.xml"))
    xml = (
        '<setup><execute uri="lib/first.scr.py"/><execute uri="lib/second.scr.py"/>'
        '<generate name="rows" count="1" target=""><key name="value" script="VALUE"/></generate></setup>'
    )
    result = CeBoundedExecutor(workspace).execute(
        BoundedExecutionRequest(xml=xml, descriptor_path=workspace.descriptor_path)
    )
    assert not result.ok
    assert not result.captured.products
    assert any("never the workspace files" in (item.remediation or "") for item in result.diagnostics)
