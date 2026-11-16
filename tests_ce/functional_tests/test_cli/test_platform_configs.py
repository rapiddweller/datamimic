# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.interfaces.cli import app, runtime

DESCRIPTOR = Path(__file__).resolve().parents[2] / "scenarios/s19_script_scope/datamimic.xml"


@pytest.mark.parametrize(
    "value,expected",
    [(None, {}), ("{}", {}), ('{"memory_limit_mb": 512}', {"memory_limit_mb": 512})],
)
def test_platform_configs_objects_and_omission(
    monkeypatch: pytest.MonkeyPatch, value: str | None, expected: dict[str, object]
) -> None:
    requests: list[RunRequest] = []
    monkeypatch.setattr(runtime, "run", requests.append)
    arguments = ["run", str(DESCRIPTOR)]
    if value is not None:
        arguments.extend(["--platform-configs", value])

    result = CliRunner().invoke(app, arguments)

    assert result.exit_code == 0, result.output
    assert len(requests) == 1
    assert requests[0].platform_configs is not None
    assert requests[0].platform_configs.root == expected


@pytest.mark.parametrize("value", ["[1]", "[]", '"bad"', "null", "0", "true"])
def test_non_object_platform_configs_fail_before_run(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    requests: list[RunRequest] = []
    monkeypatch.setattr(runtime, "run", requests.append)

    result = CliRunner().invoke(app, ["run", str(DESCRIPTOR), "--platform-configs", value])

    assert result.exit_code == 1
    assert "Error: --platform-configs must be a JSON object" in result.output
    assert "Traceback" not in result.output
    assert not requests


@pytest.mark.parametrize("value", ["{", ""])
def test_invalid_json_fails_before_run(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    requests: list[RunRequest] = []
    monkeypatch.setattr(runtime, "run", requests.append)

    result = CliRunner().invoke(app, ["run", str(DESCRIPTOR), "--platform-configs", value])

    assert result.exit_code == 1
    assert "Error: Invalid platform configuration JSON:" in result.output
    assert "Traceback" not in result.output
    assert not requests
