"""User DSL values must keep Build's typed rejection contract at every transport."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import RejectedBuild
from datamimic_ce.interfaces.cli import app
from tests_ce.authoring_project import build_project, write_project
from tests_ce.build_input_fixtures import _GATES, _entry

INVALID_GENERATIONS = (
    ('start="not-a-date" end="2026-01-01T04:00:00" interval="PT1H"', '<key name="v" constant="ok"/>', "start"),
    (
        'start="2026-01-01T00:00:00" end="2026-01-01T04:00:00" interval="P1M"',
        '<key name="v" constant="ok"/>',
        "interval",
    ),
    ('start="2026-01-01T00:00:00Z" end="2026-01-01T04:00:00" interval="PT1H"', '<key name="v" constant="ok"/>', "end"),
    ('count="1"', '<key name="v" type="float" min="3" max="1"/>', "max"),
    ('count="1"', '<key name="v" type="float" min="NaN" max="1"/>', "min"),
)


@pytest.mark.parametrize(("attributes", "fields", "attribute"), INVALID_GENERATIONS)
def test_invalid_dsl_values_return_rejected_build_and_block_gates(
    tmp_path: Path, attributes: str, fields: str, attribute: str
) -> None:
    result = build_project(tmp_path, _entry(attributes, fields), verification=_GATES)
    assert isinstance(result, RejectedBuild), result
    assert result.diagnostics[0].path[:4] == ("document", "root", "children", 0)
    assert result.diagnostics[0].path[-2:] == ("properties", attribute)
    assert result.diagnostics[0].remediation
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


@pytest.mark.parametrize(("attributes", "fields", "attribute"), INVALID_GENERATIONS)
def test_cli_invalid_dsl_values_emit_typed_json(tmp_path: Path, attributes: str, fields: str, attribute: str) -> None:
    write_project(tmp_path, _entry(attributes, fields), verification=_GATES)
    response = CliRunner().invoke(app, ["authoring", "build", str(tmp_path)])
    assert response.exit_code == 1
    result = json.loads(response.stdout)
    assert result["outcome"] == "rejected"
    assert result["phase"] == "expectation"
    assert result["diagnostics"][0]["path"][-2:] == ["properties", attribute]
    assert result["diagnostics"][0]["remediation"]


def test_time_window_validation_keeps_value_error_and_pickle_contract() -> None:
    import pickle

    from datamimic_ce.engine.dsl.api import TimeSeriesConfig, TimeSeriesConfigError

    with pytest.raises(TimeSeriesConfigError) as caught:
        TimeSeriesConfig.parse("not-a-date", "2026-01-01", "PT1H")
    error = caught.value
    restored = pickle.loads(pickle.dumps(error))
    assert isinstance(restored, ValueError)
    assert restored.attribute == "start"
    assert str(restored) == str(error)
