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


class Equivalent(BaseModel):
    """A second spelling of the project: Build is ready and a run gives the same rows as the project."""

    model_config = ConfigDict(extra="forbid")

    name: StrictStr
    patch: Patch


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: StrictStr
    proves: list[StrictStr]
    products: dict[StrictStr, StrictInt]
    negatives: list[Negative] = []
    equivalents: list[Equivalent] = []


def _load(directory: Path) -> Scenario:
    return Scenario.model_validate_json((directory / "scenario.json").read_text(encoding="utf-8"))


_DIRECTORIES = sorted(path.parent for path in _ROOT.glob("*/scenario.json"))
_NEGATIVES = [(path, negative) for path in _DIRECTORIES for negative in _load(path).negatives]
_EQUIVALENTS = [(path, equivalent) for path in _DIRECTORIES for equivalent in _load(path).equivalents]


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
_COMMA_SEPARATOR = re.compile(r"""[sS]eparator\s*=\s*(["']),\1""")
_NAME = "a data file must be *.ent.csv or *.wgt.csv"
_WEIGHTING = "a *.wgt.csv file must sit in data/weighting/"
_ENTITY = "an *.ent.csv file must sit in data/entity/ or data/fixtures/"
_SEPARATOR = 'separator="," overrides the default pipe separator'
_PARAMETERS = "a *.properties file must sit in conf/"
_DATA_FOLDER = "a file in data/ must sit in data/entity/, data/weighting/ or data/fixtures/"
_STEP = "a step must be model/<nn>_<activity>.xml, or delivery/<nn>_<activity>.xml with nn 90 to 99"
_STEP_NAME = {("model",): re.compile(r"\d\d_"), ("delivery",): re.compile(r"9\d_")}


def _data_standard_findings(root: Path) -> list[str]:
    """plugins/datamimic/skills/generate-test-data/references/project-structure.md: checks the data file names and
    folders, the parameter folder, the step names and the comma separator. One finding per file: the first broken
    rule. <scenario>/output/ is what a local datamimic run writes, not project data."""
    found = []
    for path in sorted(root.rglob("*")):
        name = path.relative_to(root)
        if name.parts[1:2] == ("output",) or not path.is_file():
            continue
        folder = name.parent.parts[1:]
        step_name = _STEP_NAME.get(folder)
        if path.suffix == ".csv" and not path.name.endswith((".ent.csv", ".wgt.csv")):
            found.append(f"{name}: {_NAME}")
        elif path.suffix == ".csv" and ".wgt" in path.suffixes:  # x.wgt.ent.csv is a weighted entity file
            if folder != ("data", "weighting"):
                found.append(f"{name}: {_WEIGHTING}")
        elif path.suffix == ".csv" and folder not in {("data", "entity"), ("data", "fixtures")}:
            found.append(f"{name}: {_ENTITY}")
        elif path.suffix == ".properties" and folder != ("conf",):
            found.append(f"{name}: {_PARAMETERS}")
        elif folder[:1] == ("data",) and folder[1:2] not in {("entity",), ("weighting",), ("fixtures",)}:
            found.append(f"{name}: {_DATA_FOLDER}")
        elif path.suffix == ".xml" and _COMMA_SEPARATOR.search(path.read_text(encoding="utf-8")):
            found.append(f"{name}: {_SEPARATOR}")
        elif path.suffix == ".xml" and step_name is not None and not step_name.match(path.name):
            found.append(f"{name}: {_STEP}")
    return found


def test_scenario_data_follows_the_project_data_standard() -> None:
    found = _data_standard_findings(_ROOT)
    assert not found, "\n".join(found)


@pytest.mark.parametrize(
    ("file", "content", "reason"),
    [
        ("s99/data/entity/x.ent.csv", "id\n1\n", None),
        ("s99/data/fixtures/x.ent.csv", "id\n1\n", None),
        ("s99/data/weighting/x.wgt.csv", "a|1\n", None),
        ("s99/data/weighting/x.wgt.ent.csv", "id\n1\n", None),
        ("s99/output/x.csv", "a,b\n", None),
        ("README.md", "root file\n", None),
        ("s99/x.ent.csv", "id\n1\n", _ENTITY),
        ("s99/fixtures/x.ent.csv", "id\n1\n", _ENTITY),
        ("s99/data/entity/x.wgt.csv", "a|1\n", _WEIGHTING),
        ("s99/data/entity/x.wgt.ent.csv", "id\n1\n", _WEIGHTING),
        ("s99/x.csv", "a,b\n", _NAME),
        ("s99/data/output/x.csv", "a,b\n", _NAME),
        ("s99/datamimic.xml", '<setup defaultSeparator=","/>', _SEPARATOR),
        ("s99/datamimic.xml", "<setup><generate separator = ','/></setup>", _SEPARATOR),
        ("s99/conf/base.properties", "a=1\n", None),
        ("s99/data/entity/x.json", "[]\n", None),
        ("s99/model/10_x.xml", "<setup/>", None),
        ("s99/delivery/90_x.xml", "<setup/>", None),
        ("s99/delivery/99_x.xml", "<setup/>", None),
        ("s99/data/x.properties", "a=1\n", _PARAMETERS),
        ("s99/x.properties", "a=1\n", _PARAMETERS),
        ("s99/data/x.json", "[]\n", _DATA_FOLDER),
        ("s99/data/other/x.json", "[]\n", _DATA_FOLDER),
        ("s99/model/x.xml", "<setup/>", _STEP),
        ("s99/model/1_x.xml", "<setup/>", _STEP),
        ("s99/model/100_x.xml", "<setup/>", _STEP),
        ("s99/model/_x.xml", "<setup/>", _STEP),
        ("s99/model/ab_x.xml", "<setup/>", _STEP),
        ("s99/delivery/89_x.xml", "<setup/>", _STEP),
        ("s99/delivery/100_x.xml", "<setup/>", _STEP),
    ],
)
def test_data_standard_guard_names_the_one_broken_rule(
    file: str, content: str, reason: str | None, tmp_path: Path
) -> None:
    (tmp_path / file).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / file).write_text(content, encoding="utf-8")
    assert _data_standard_findings(tmp_path) == ([] if reason is None else [f"{Path(file)}: {reason}"])


@pytest.mark.parametrize(
    ("directory", "equivalent"),
    _EQUIVALENTS,
    ids=[f"{path.name}/{equivalent.name}" for path, equivalent in _EQUIVALENTS],
)
def test_equivalent_spelling_gives_the_same_rows(
    directory: Path, equivalent: Equivalent, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _copy(directory, tmp_path / "project")
    variant = _copy(directory, tmp_path / "variant")
    _apply(equivalent.patch, variant)
    built = _build(variant)
    assert isinstance(built, ReadyBuild), [(str(item.code), item.message) for item in built.diagnostics]

    monkeypatch.chdir(project)
    rows = _run(project)
    monkeypatch.chdir(variant)
    assert _run(variant) == rows, "the two spellings must give identical rows for the same seed"


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
