# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Run every scenario directory (README.md holds the contract). The projects are the test; this module only
copies, Builds, runs and compares."""

import re
import shutil
from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr, model_validator

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
    patch: Patch | None = None
    # A directory of whole files copied over the project; only for a change that one patch cannot express.
    dir: StrictStr | None = None
    diagnostic: StrictStr
    expected: StrictStr | None = None
    # A normal run of the variant must also stop, with an error that contains this text.
    run_error: StrictStr | None = None

    @model_validator(mode="after")
    def _one_change(self) -> "Negative":
        if (self.patch is None) == (self.dir is None):
            raise ValueError(f"negative {self.name} must give exactly one of patch or dir")
        return self


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


def _apply(negative: Negative, directory: Path, project: Path) -> None:
    if negative.dir is not None:
        shutil.copytree(directory / negative.dir, project, dirs_exist_ok=True)
        return
    assert negative.patch is not None
    target = project / negative.patch.file
    text = target.read_text(encoding="utf-8")
    assert text.count(negative.patch.old) == 1, f"{negative.patch.file} must contain the old text exactly once"
    target.write_text(text.replace(negative.patch.old, negative.patch.new), encoding="utf-8")


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
    _apply(negative, directory, project)
    rejected = _build(project)
    assert isinstance(rejected, RejectedBuild), "Build accepted a variant that must be rejected"
    codes = [str(item.code) for item in rejected.diagnostics]
    assert negative.diagnostic in codes, f"expected {negative.diagnostic}, Build reported {codes}"
    if negative.expected is not None:  # one code covers many rules; the expectation text names the rule
        named = [str(item.expected) for item in rejected.diagnostics if str(item.code) == negative.diagnostic]
        assert negative.expected in named, f"expected {negative.expected!r}, Build reported {named}"
    if negative.run_error is not None:
        monkeypatch.chdir(project)
        with pytest.raises(TaskConfigError, match=re.escape(negative.run_error)):
            _run(project)
