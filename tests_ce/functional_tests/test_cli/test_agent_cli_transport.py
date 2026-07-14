"""Black-box contracts for agents invoking the installed ``datamimic`` CLI.

These tests intentionally spawn the console script with a PATH that cannot find a
second/global ``datamimic`` installation.  They cover transport behavior that
``CliRunner`` cannot prove: stdout/stderr separation and repeatability across real
processes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def _console_script() -> Path:
    script = Path(sys.executable).with_name("datamimic")
    assert script.is_file(), f"DATAMIMIC console script not installed next to {sys.executable}"
    return script


def _run_cli(
    cwd: Path,
    *args: str,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = "/usr/bin:/bin"
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [_console_script(), *args],
        cwd=cwd,
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_capabilities_is_repeatable_pure_json_without_global_cli(tmp_path: Path) -> None:
    first = _run_cli(tmp_path, "capabilities")
    second = _run_cli(tmp_path, "capabilities")

    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == ""
    assert first.stdout == second.stdout
    manifest = json.loads(first.stdout)
    assert manifest["schema_version"]
    assert manifest["aliases"]["iterate"] == "generate"
    assert "iterate" in manifest["elements"]
    assert {"kafka-exporter", "object-storage", "operate"}.isdisjoint(manifest["elements"])


@pytest.mark.parametrize(
    ("command", "message"),
    [
        (("lint", "model.xml", "--format", "json", "--fail-on", "banana"), "Invalid fail-on"),
        (("lint", "model.xml", "--format", "json", "--max-diagnostics", "0"), "Invalid max-diagnostics"),
        (("dry-run", "model.xml", "--format", "json", "--max-count", "0"), "Invalid max-count"),
        (("dry-run", "model.xml", "--format", "json", "--sample-rows", "0"), "Invalid sample-rows"),
        (("dry-run", "model.xml", "--format", "json", "--timeout", "0"), "Invalid timeout"),
    ],
)
def test_invalid_agent_options_are_single_json_errors(
    tmp_path: Path,
    command: tuple[str, ...],
    message: str,
) -> None:
    (tmp_path / "model.xml").write_text("<setup/>", encoding="utf-8")

    result = _run_cli(tmp_path, *command)

    assert result.returncode == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert message in payload["error"]


def test_seeded_json_dry_run_is_repeatable_and_stderr_clean(tmp_path: Path) -> None:
    descriptor = tmp_path / "model.xml"
    descriptor.write_text(
        '<setup rngSeed="17">'
        '<generate name="records" count="8">'
        '<key name="id" generator="IncrementGenerator"/>'
        '<key name="score" type="int" min="10" max="20"/>'
        "</generate>"
        "</setup>",
        encoding="utf-8",
    )

    first = _run_cli(tmp_path, "dry-run", "model.xml", "--format", "json")
    second = _run_cli(tmp_path, "dry-run", "model.xml", "--format", "json")

    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == ""
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["ok"] is second_payload["ok"] is True
    assert first_payload["stage"] == second_payload["stage"] == "run"
    assert first_payload["products"] == second_payload["products"]


@pytest.mark.parametrize("stdin", ["", "{broken", "[]"])
def test_malformed_scaffold_stdin_is_single_json_error(tmp_path: Path, stdin: str) -> None:
    result = _run_cli(tmp_path, "scaffold", "-", "--format", "json", stdin=stdin)

    assert result.returncode == 2
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["error"]
