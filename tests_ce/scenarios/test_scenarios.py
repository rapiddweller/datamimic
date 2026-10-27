# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Run every scenario directory (README.md holds the contract). The projects are the test; this module only
copies, Builds, runs and compares."""

import re
import shutil
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, BuildResult, ReadyBuild, RejectedBuild
from datamimic_ce.errors.base import TaskConfigError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_ROOT = Path(__file__).resolve().parent


class Patch(BaseModel):
    """Replace one text in one file of the copied project. The text must occur exactly once."""

    model_config = ConfigDict(extra="forbid")

    file: StrictStr
    old: StrictStr
    new: StrictStr


class Negative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: StrictStr
    patch: Patch
    diagnostic: StrictStr
    expected: StrictStr | None = None
    # The catalog issue code of a runtime refusal, which Build reports as the diagnostic's ce_error.
    issue: StrictStr | None = None
    # A normal run of the variant must also stop, with an error that contains this text.
    run_error: StrictStr | None = None


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: StrictStr
    proves: list[StrictStr]
    products: dict[StrictStr, StrictInt]
    negatives: list[Negative] = []


def _load(directory: Path) -> Scenario:
    return Scenario.model_validate_json((directory / "scenario.json").read_text(encoding="utf-8"))


_DIRECTORIES = sorted(path.parent for path in _ROOT.glob("*/scenario.json"))
_NEGATIVES = [(path, negative) for path in _DIRECTORIES for negative in _load(path).negatives]


def _copy(source: Path, destination: Path) -> Path:
    shutil.copytree(source, destination)
    return destination


def _apply(patch: Patch, project: Path) -> None:
    target = (project / patch.file).resolve()
    assert target.is_relative_to(project.resolve()), f"{patch.file} must stay inside the project copy"
    text = target.read_text(encoding="utf-8")
    assert text.count(patch.old) == 1, f"{patch.file} must contain the old text exactly once"
    target.write_text(text.replace(patch.old, patch.new), encoding="utf-8")


def _build(project: Path) -> BuildResult:
    return create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()


def _run(project: Path) -> dict[str, list[object]]:
    engine = DataMimicTest(test_dir=project, filename=PROJECT_ENTRY_PATH, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result() or {}


@pytest.mark.parametrize("directory", _DIRECTORIES, ids=lambda path: path.name)
def test_scenario_builds_runs_and_replays(directory: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    scenario = _load(directory)
    project = _copy(directory, tmp_path / directory.name)
    monkeypatch.chdir(project)  # file and SQLite products resolve against the working directory

    built = _build(project)
    assert isinstance(built, ReadyBuild), [(str(item.code), item.message) for item in built.diagnostics]

    first = _run(project)
    counts = {name: len(rows) for name, rows in first.items() if name in scenario.products}
    assert counts == scenario.products
    assert _run(project) == first, "a second run with the same seed must give identical rows"


@pytest.mark.parametrize(
    ("directory", "negative"),
    _NEGATIVES,
    ids=[f"{path.name}/{negative.name}" for path, negative in _NEGATIVES],
)
def test_negative_is_rejected_with_named_diagnostic(
    directory: Path, negative: Negative, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _copy(directory, tmp_path / "variant")
    _apply(negative.patch, project)
    rejected = _build(project)
    assert isinstance(rejected, RejectedBuild), "Build accepted a variant that must be rejected"
    codes = [str(item.code) for item in rejected.diagnostics]
    assert negative.diagnostic in codes, f"expected {negative.diagnostic}, Build reported {codes}"
    if negative.expected is not None:  # one code covers many rules; the expectation text names the rule
        named = [str(item.expected) for item in rejected.diagnostics if str(item.code) == negative.diagnostic]
        assert negative.expected in named, f"expected {negative.expected!r}, Build reported {named}"
    if negative.issue is not None:
        issues = [
            str(item.ce_error.issue_code)
            for item in rejected.diagnostics
            if str(item.code) == negative.diagnostic and item.ce_error is not None
        ]
        assert negative.issue in issues, f"expected issue {negative.issue}, Build reported {issues}"
    if negative.run_error is not None:
        monkeypatch.chdir(project)
        with pytest.raises(TaskConfigError, match=re.escape(negative.run_error)):
            _run(project)


# Both quote styles; a separator other than the comma is not this guard's concern.
_COMMA_SEPARATOR = re.compile(r"""(?:default)?[sS]eparator\s*=\s*(["']),\1""")


def test_scenario_data_follows_the_project_data_standard() -> None:
    """plugins/datamimic/skills/generate-test-data/references/project-structure.md: data files are *.ent.csv or
    *.wgt.csv, separated by the default pipe. output/ is what a local datamimic run writes, not project data."""
    found = []
    for path in sorted(_ROOT.rglob("*")):
        name = path.relative_to(_ROOT)
        if "output" in name.parts or not path.is_file():
            continue
        if path.suffix == ".csv" and not path.name.endswith((".ent.csv", ".wgt.csv")):
            found.append(f"{name}: a data file must be *.ent.csv or *.wgt.csv")
        elif path.suffix == ".xml" and _COMMA_SEPARATOR.search(path.read_text(encoding="utf-8")):
            found.append(f'{name}: separator="," overrides the default pipe separator')
    assert not found, "\n".join(found)


@pytest.mark.parametrize("escape", ["absolute", "parent"])
def test_patch_outside_the_project_copy_is_refused(escape: str, tmp_path: Path) -> None:
    project = tmp_path / "variant"
    project.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("old", encoding="utf-8")
    file = str(outside) if escape == "absolute" else "../outside.txt"

    with pytest.raises(AssertionError, match="inside the project copy"):
        _apply(Patch(file=file, old="old", new="new"), project)
    assert outside.read_text(encoding="utf-8") == "old"
