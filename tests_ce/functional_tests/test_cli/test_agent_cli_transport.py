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

from datamimic_ce.authoring.domain.requests import PROJECT_ACCEPTANCE_PATH
from tests_ce.authoring_project import write_project


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
    first = _run_cli(tmp_path, "authoring", "capabilities")
    second = _run_cli(tmp_path, "authoring", "capabilities")

    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == ""
    assert first.stdout == second.stdout
    manifest = json.loads(first.stdout)
    assert "generate" in manifest["element"]
    assert {"kafka-exporter", "object-storage", "operate"}.isdisjoint(manifest["element"])


def test_module_invocation_preserves_success_and_usage_exit_codes(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parents[3])

    success = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", "authoring", "capabilities"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    invalid_command = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", "unknown-command"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert success.returncode == 0
    assert success.stderr == ""
    assert "generate" in json.loads(success.stdout)["element"]
    assert invalid_command.returncode == 2
    assert "Usage:" in invalid_command.stderr


@pytest.mark.parametrize("options", [("--max-count", "0"), ("--sample-rows", "0"), ("--timeout", "0")])
def test_invalid_agent_options_are_single_json_errors(tmp_path: Path, options: tuple[str, ...]) -> None:
    (tmp_path / "model.xml").write_text("<setup/>", encoding="utf-8")
    result = _run_cli(tmp_path, "authoring", "dry-run", "model.xml", *options)
    assert result.returncode == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["diagnostics"]


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

    first = _run_cli(tmp_path, "authoring", "dry-run", "model.xml", "--format", "json")
    second = _run_cli(tmp_path, "authoring", "dry-run", "model.xml", "--format", "json")

    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == ""
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["ok"] is second_payload["ok"] is True
    assert first_payload["phase"] == second_payload["phase"] == "dry_run"
    assert first_payload["products"] == second_payload["products"]


def test_seeded_json_build_is_repeatable_and_stderr_clean(tmp_path: Path) -> None:
    write_project(
        tmp_path,
        '<setup rngSeed="17"><generate name="records" count="8">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>',
    )
    first = _run_cli(tmp_path, "authoring", "build", ".")
    second = _run_cli(tmp_path, "authoring", "build", ".")
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == ""
    assert first.stdout == second.stdout
    payload = json.loads(first.stdout)
    assert payload["outcome"] == "ready"
    assert payload["evidence"][0]["count"] == 8


@pytest.mark.parametrize("acceptance", ["", "{broken", "[]"])
def test_malformed_acceptance_is_single_json_rejection(tmp_path: Path, acceptance: str) -> None:
    write_project(tmp_path, "<setup/>")
    (tmp_path / PROJECT_ACCEPTANCE_PATH).write_text(acceptance, encoding="utf-8")
    result = _run_cli(tmp_path, "authoring", "build", ".")

    assert result.returncode == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["outcome"] == "rejected"
    assert payload["diagnostics"]
