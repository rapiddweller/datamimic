"""One owner for the NAME=VALUE syntax and the name rule of `run --param` and `authoring run-project --param`."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.domain.project_run import ProjectParam, ProjectRunRequest
from datamimic_ce.interfaces.cli import app

runner = CliRunner()

# Equivalence classes of a --param entry that is invalid before any work happens.
INVALID_ENTRIES = [
    pytest.param("novalue", id="missing-equals"),
    pytest.param("=value", id="empty-name"),
    pytest.param("class=x", id="keyword-name"),
    pytest.param("1abc=x", id="digit-first-name"),
    pytest.param("a-b=x", id="punctuation-name"),
]


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        pytest.param("STAGE=test", ("STAGE", "test"), id="valid"),
        pytest.param("EMPTY=", ("EMPTY", ""), id="empty-value"),
        pytest.param("label=a=b=c", ("label", "a=b=c"), id="value-with-equals"),
        pytest.param("_x1=v", ("_x1", "v"), id="underscore-name"),
    ],
)
def test_owner_accepts_valid_entries(entry: str, expected: tuple[str, str]) -> None:
    assert ProjectParam.parse(entry) == ProjectParam(name=expected[0], value=expected[1])


@pytest.mark.parametrize("entry", INVALID_ENTRIES)
def test_owner_rejects_invalid_entries(entry: str) -> None:
    with pytest.raises(ValueError):
        ProjectParam.parse(entry)


def test_request_rejects_duplicate_names() -> None:
    with pytest.raises(ValueError, match="Duplicate runtime property: a"):
        ProjectRunRequest(params=(ProjectParam(name="a", value="1"), ProjectParam(name="a", value="2")))


@pytest.mark.parametrize("entry", INVALID_ENTRIES)
def test_run_and_run_project_reject_the_same_entries_with_exit_2(tmp_path: Path, entry: str) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text("<setup/>", encoding="utf-8")
    (tmp_path / "acceptance").mkdir()

    run = runner.invoke(app, ["run", str(descriptor), "--param", entry])
    run_project = runner.invoke(app, ["authoring", "run-project", str(tmp_path), "--param", entry])

    assert run.exit_code == 2
    assert run_project.exit_code == 2
    result = json.loads(run_project.stdout)
    assert result["outcome"] == "not_run"
    assert result["not_run_reason"] == "input"


def test_run_project_rejects_duplicate_names_with_exit_2_before_work(tmp_path: Path) -> None:
    (tmp_path / "datamimic.xml").write_text("<setup/>", encoding="utf-8")
    result = runner.invoke(app, ["authoring", "run-project", str(tmp_path), "--param", "a=1", "--param", "a=2"])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["not_run_reason"] == "input"


def test_run_duplicate_stays_exit_2(tmp_path: Path) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text("<setup/>", encoding="utf-8")
    result = runner.invoke(app, ["run", str(descriptor), "--param", "a=1", "--param", "a=2"])
    assert result.exit_code == 2
