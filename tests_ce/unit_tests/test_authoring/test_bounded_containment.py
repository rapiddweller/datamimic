# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A bounded run writes only inside its private directory and starts no process (#361)."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest

_MODELS = Path(__file__).parent / "bounded_containment_models"


def _run(root: Path, script: str, *, allow_side_effects: bool = False):
    xml = f'<setup><generate name="rows" count="1" target=""><key name="value" script="{script}"/></generate></setup>'
    return _execute(root, xml, allow_side_effects=allow_side_effects)


def _execute(root: Path, xml: str, *, allow_side_effects: bool = False):
    workspace = AuthoringWorkspaceContext(root, PurePosixPath("model.xml"))
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


def test_a_native_refusal_is_reported_not_lost(tmp_path: Path) -> None:
    # numpy turns the refused audit event into a bare SystemError; the run must still say what failed.
    (tmp_path / "workspace").mkdir()
    outside = tmp_path / "array.bin"
    result = _run(tmp_path / "workspace", f"np.zeros(3).tofile('{outside.as_posix()}')")
    assert not result.ok
    assert not outside.exists()
    assert all(item.message != "Bounded child returned invalid capture evidence." for item in result.diagnostics)


def test_the_run_cannot_forge_its_reply(tmp_path: Path) -> None:
    result = _run(tmp_path, "pd.DataFrame([{'a': 1}]).to_csv('../reply.pickle')")
    assert not result.ok
    assert all(item.message != "Bounded child returned invalid capture evidence." for item in result.diagnostics)


def test_a_relative_write_through_an_outside_directory_descriptor_is_refused(tmp_path: Path) -> None:
    (tmp_path / "workspace").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    flags = "os.O_CREAT | os.O_WRONLY"
    result = _run(
        tmp_path / "workspace", f"os.open('escaped', {flags}, dir_fd=os.open('{outside.as_posix()}', os.O_RDONLY))"
    )
    assert not result.ok
    assert not (outside / "escaped").exists()


def test_a_checked_directory_cannot_be_renamed_away_and_back(tmp_path: Path) -> None:
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "second.scr.py").write_text("VALUE = 1\n", encoding="utf-8")
    result = _run(tmp_path, "os.rename('lib', 'moved')")
    assert not result.ok


def test_unaudited_node_creation_is_refused(tmp_path: Path) -> None:
    (tmp_path / "workspace").mkdir()
    for call in ("mknod", "mkfifo"):
        node = tmp_path / call
        result = _run(tmp_path / "workspace", f"os.{call}('{node.as_posix()}')")
        assert not result.ok
        assert not node.exists()


def test_the_null_device_is_only_writable(tmp_path: Path) -> None:
    # sys.audit raises the event itself, so the OS permission on the null device does not decide the outcome.
    probe = (
        "import os, sys\n"
        "from pathlib import Path\n"
        "from datamimic_ce.authoring.adapters.bounded_executor_child import _contain\n"
        "_contain(Path(sys.argv[1]), Path(sys.argv[1]), ())\n"
        "open(os.devnull, 'w').close()\n"
        "try:\n"
        "    sys.audit('os.chmod', os.devnull, 0o666, -1)\n"
        "except PermissionError:\n"
        "    print('refused')\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe, str(tmp_path)], capture_output=True, text=True, check=True, timeout=60
    )
    assert completed.stdout.strip() == "refused", completed.stderr


def test_file_descriptor_forms_of_path_operations_are_refused(tmp_path: Path) -> None:
    (tmp_path / "workspace").mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    before = outside.stat().st_mode
    result = _run(tmp_path / "workspace", f"os.chmod(os.open('{outside.as_posix()}', os.O_RDONLY), 0o600)")
    assert not result.ok
    assert outside.stat().st_mode == before


def test_a_relative_remove_through_an_outside_directory_descriptor_is_refused(tmp_path: Path) -> None:
    (tmp_path / "workspace").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "victim").write_text("x", encoding="utf-8")
    result = _run(tmp_path / "workspace", f"os.remove('victim', dir_fd=os.open('{outside.as_posix()}', os.O_RDONLY))")
    assert not result.ok
    assert (outside / "victim").exists()


@pytest.mark.skipif(os.name != "posix", reason="the models use POSIX paths and AF_UNIX sockets")
@pytest.mark.parametrize("model", sorted((_MODELS / "accepted").glob("*.xml")), ids=lambda path: path.stem)
def test_an_accepted_model_runs_inside_the_private_workspace(tmp_path: Path, model: Path) -> None:
    result = _execute(tmp_path, model.read_text(encoding="utf-8"))
    assert result.ok, result.diagnostics
    assert not any(tmp_path.iterdir()), "the private copy, not the workspace, received every write"


@pytest.mark.skipif(os.name != "posix", reason="the models use POSIX paths and AF_UNIX sockets")
@pytest.mark.parametrize("model", sorted((_MODELS / "refused").glob("*.xml")), ids=lambda path: path.stem)
def test_a_refused_model_leaves_no_trace_outside_the_private_workspace(tmp_path: Path, model: Path) -> None:
    # /tmp keeps the socket path under the 104-byte AF_UNIX limit that macOS enforces before the audit event.
    with tempfile.TemporaryDirectory(prefix="dm363", dir="/tmp") as outside:
        xml = model.read_text(encoding="utf-8").replace("@OUTSIDE@", outside)
        result = _execute(tmp_path, xml)
        assert not result.ok
        assert any(
            "writes only new files inside its private workspace" in (item.remediation or "")
            for item in result.diagnostics
        )
        assert not list(Path(outside).iterdir())
