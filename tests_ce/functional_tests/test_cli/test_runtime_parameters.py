"""External runtime properties and separated pseudonymization keys through the real CLI."""

from __future__ import annotations

import hmac
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.interfaces.cli import app

runner = CliRunner()
KEY = "example-test-material-32-bytes-long"


def _descriptor(directory: Path, seed: int = 7) -> Path:
    path = directory / "model.xml"
    path.write_text(
        f'''<setup rngSeed="{seed}">
  <generate name="hashed" count="3" target="JSON">
    <key name="number" type="int" min="1" max="1000000"/>
    <key name="label" script="label"/>
    <key name="token" constant="known-input"
         converter="Hash('sha256','hex',key=pseudonym_key.encode('utf-8'))"/>
  </generate>
</setup>''',
        encoding="utf-8",
    )
    return path


def _rows(directory: Path, task: str) -> list[dict]:
    files = list((directory / "output" / task).rglob("*.json"))
    assert len(files) == 1
    return json.loads(files[0].read_text())


def _run_cli(directory: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", "run", *arguments],
        cwd=directory,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[3])},
        capture_output=True,
        text=True,
        timeout=45,
    )


def test_external_key_replays_across_generation_seeds_and_rotation_does_not_change_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CE_TEST_PSEUDONYM_KEY", KEY)
    conf = tmp_path / "conf"
    conf.mkdir()
    (conf / "environment.env.properties").write_text("label=from-file\npseudonym_key=unused-file-key\n")

    def generate(task: str, seed: int, key: str | None = None) -> list[dict]:
        descriptor = _descriptor(tmp_path, seed)
        key_arg = ["--param-env", "pseudonym_key=CE_TEST_PSEUDONYM_KEY"]
        if key is not None:
            key_arg = ["--param", f"pseudonym_key={key}"]
        result = _run_cli(
            tmp_path, str(descriptor), "--task-id", task, "--param", "label=override=retained", *key_arg
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert KEY not in result.stdout + result.stderr
        return _rows(tmp_path, task)

    first = generate("first", 7)
    replay = generate("replay", 7)
    changed_seed = generate("changed_seed", 8)
    rotated = generate("rotated", 7, "different-example-key-material-32bytes")

    expected = hmac.new(KEY.encode(), b"known-input", "sha256").hexdigest()
    assert {row["token"] for row in first + replay + changed_seed} == {expected}
    assert replay == first
    assert {row["token"] for row in rotated}.isdisjoint({expected})
    assert [row["number"] for row in rotated] == [row["number"] for row in first]
    assert [row["number"] for row in changed_seed] != [row["number"] for row in first]
    assert {row["label"] for row in first + replay + changed_seed + rotated} == {"override=retained"}


@pytest.mark.parametrize(
    "arguments,message",
    [
        (["--param", "malformed-private-value"], "NAME=VALUE"),
        (["--param", "=private-value"], "name"),
        (["--param", "invalid-name=private-value"], "name"),
        (["--param", "class=private-value"], "name"),
        (["--param", "name=private-value", "--param", "name=another-private-value"], "Duplicate"),
        (["--param-env", "name="], "environment"),
        (["--param-env", "name=BAD-ENV"], "environment"),
        (["--param-env", "name=CE_MISSING_PARAMETER_ENV"], "not set"),
        (["--param", "name=private-value", "--param-env", "name=CE_TEST_PARAMETER_ENV"], "Duplicate"),
    ],
)
def test_invalid_parameters_fail_before_execution_without_echoing_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, arguments: list[str], message: str
) -> None:
    monkeypatch.setenv("CE_TEST_PARAMETER_ENV", "another-private-value")
    monkeypatch.delenv("CE_MISSING_PARAMETER_ENV", raising=False)
    descriptor = _descriptor(tmp_path)

    result = runner.invoke(app, ["run", str(descriptor), *arguments])

    assert result.exit_code == 2
    assert message in result.output
    assert "private-value" not in result.output
    assert not (tmp_path / "output").exists()


def test_short_external_key_subprocess_failure_keeps_secret_out_of_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    descriptor = _descriptor(tmp_path)
    secret = "short-private-material"
    monkeypatch.setenv("CE_TEST_SHORT_KEY", secret)
    result = _run_cli(
        tmp_path, str(descriptor), "--param-env", "pseudonym_key=CE_TEST_SHORT_KEY", "--param", "label=test"
    )

    assert result.returncode != 0
    assert "at least 32 bytes" in result.stdout + result.stderr
    assert secret not in result.stdout + result.stderr
    assert not (tmp_path / "output").exists()
