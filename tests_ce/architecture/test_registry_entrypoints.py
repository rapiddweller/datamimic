"""Fresh-process probes for cold CLI-to-registry composition."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _cli(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", *arguments],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _cold_script(cwd: Path, script: str) -> subprocess.CompletedProcess[str]:
    program = cwd / "cold_registry_probe.py"
    program.write_text(script, encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    return subprocess.run(
        [sys.executable, program.name],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_cli_entrypoints_resolve_live_registries_outside_checkout(tmp_path: Path) -> None:
    """A cold process must compose the canonical CLI and live registries."""
    valid = tmp_path / "valid.xml"
    unsupported = tmp_path / "unsupported.xml"
    valid.write_text(
        '<setup rngSeed="1"><generate name="things" count="1">'
        '<key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    unsupported.write_text('<setup rngSeed="1"><not-registered/></setup>', encoding="utf-8")

    capabilities = _cli(tmp_path, "capabilities", "--full")
    assert capabilities.returncode == 0, capabilities.stderr
    manifest = json.loads(capabilities.stdout)
    assert {"setup", "generate", "key"} <= set(manifest["elements"])
    assert manifest["targets"]

    accepted = _cli(tmp_path, "lint", valid.name, "--format", "json")
    assert accepted.returncode == 0, accepted.stderr
    assert json.loads(accepted.stdout)["ok"] is True

    rejected = _cli(tmp_path, "lint", unsupported.name, "--format", "json")
    assert rejected.returncode == 1
    diagnostics = json.loads(rejected.stdout)["diagnostics"]
    assert any(diagnostic["rule"] == "DM101" for diagnostic in diagnostics)


def test_cold_task_dispatch_keeps_statement_fallback_and_custom_registration(tmp_path: Path) -> None:
    """Task composition must not erase the generic fallback or extension registrations."""
    result = _cold_script(
        tmp_path,
        """
import importlib

from datamimic_ce.engine.dsl.api import Statement
from datamimic_ce.engine.runtime.tasks.base.dispatch import create_task
import datamimic_ce.engine.runtime.tasks as tasks

try:
    create_task(Statement("unknown", None), None)
except ValueError as error:
    assert str(error) == "Cannot create a task for statement Statement"
else:
    raise AssertionError("generic Statement dispatch must reject unsupported statements")

class CustomStatement(Statement):
    pass

@create_task.register(CustomStatement)
def create_custom_task(statement, context, pagination=None):
    return "custom-task"

assert create_task(CustomStatement("custom", None), None) == "custom-task"
importlib.reload(tasks)
assert create_task(CustomStatement("custom", None), None) == "custom-task"
""",
    )

    assert result.returncode == 0, result.stderr


def test_cold_multiprocessing_worker_dispatches_key_tasks(tmp_path: Path) -> None:
    """A spawned worker must compose task registrations without the parent process state."""
    result = _cold_script(
        tmp_path,
        """
import json
import os
from pathlib import Path

from datamimic_ce.engine.dsl.api import GenerateStatement, Statement
from datamimic_ce.engine.runtime.api import run
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.engine.runtime.tasks.base.dispatch import create_task
from datamimic_ce.engine.runtime.tasks.base.task import GenSubTask


class PidStatement(Statement):
    pass


class PidTask(GenSubTask):
    def __init__(self, statement):
        self._statement = statement

    @property
    def statement(self):
        return self._statement

    def execute(self, context):
        context.add_current_product_field("pid", os.getpid())


@create_task.register(PidStatement)
def create_pid_task(statement, context, pagination=None):
    return PidTask(statement)


def add_pid_statement(setup):
    generate = next(statement for statement in setup.sub_statements if isinstance(statement, GenerateStatement))
    generate.sub_statements.append(PidStatement("pid", generate))


def main() -> None:
    descriptor = Path("model.xml")
    descriptor.write_text(
        '<setup numProcess="2"><generate name="rows" count="4" pageSize="1" '
        'target="" mpPlatform="multiprocessing"/></setup>',
        encoding="utf-8",
    )
    result = run(RunRequest(descriptor, test_mode=True, statement_transformer=add_pid_statement))
    assert result.captured is not None
    assert type(result.captured) is dict
    rows = result.captured["rows"]
    assert type(rows) is list
    assert len(rows) == 4
    assert all(type(row) is dict for row in rows)
    Path("pids.json").write_text(
        json.dumps({"parent_pid": os.getpid(), "worker_pids": [row["pid"] for row in rows]}),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
""",
    )

    assert result.returncode == 0, result.stderr
    pids = json.loads((tmp_path / "pids.json").read_text(encoding="utf-8"))
    assert len(pids["worker_pids"]) == 4
    assert set(pids["worker_pids"]) - {pids["parent_pid"]}
