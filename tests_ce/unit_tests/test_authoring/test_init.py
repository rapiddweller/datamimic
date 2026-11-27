# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""`datamimic authoring init` writes a starter project that Build proves as written, and never overwrites."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters import workspace
from datamimic_ce.authoring.adapters.workspace import write_project_scaffold
from datamimic_ce.authoring.domain.project_scaffold import ProjectInitResult, ProjectPattern, ProjectScaffold
from datamimic_ce.authoring.domain.requests import PROJECT_ACCEPTANCE_PATH, PROJECT_ENTRY_PATH, ReadyBuild
from datamimic_ce.interfaces.cli import app
from datamimic_ce.interfaces.cli.presenter import NEXT_STEP_HINT
from datamimic_ce.interfaces.project import create_project_structure


def _init(project: Path, *extra: str):
    return CliRunner().invoke(app, ["authoring", "init", str(project), "--format", "text", *extra])


def test_init_defaults_to_the_json_result_that_the_mcp_tool_returns(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["authoring", "init", str(tmp_path / "shop")])

    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == {
        "outcome": "written",
        "pattern": "flat",
        "files": ["datamimic.xml", "acceptance/build.json"],
        "diagnostics": [],
    }
    assert (
        result.stdout
        == ProjectInitResult.written(ProjectPattern.FLAT, scaffold_paths()).model_dump_json(indent=2) + "\n"
    )


def test_init_json_reports_a_refusal_with_exit_code_one_and_writes_nothing(tmp_path: Path) -> None:
    (tmp_path / PROJECT_ENTRY_PATH).write_text("mine", encoding="utf-8")

    result = CliRunner().invoke(app, ["authoring", "init", str(tmp_path)])

    payload = json.loads(result.stdout)
    assert result.exit_code == 1
    assert payload["outcome"] == "not_written"
    assert "these files exist already: datamimic.xml" in payload["diagnostics"][0]["message"]
    assert not (tmp_path / PROJECT_ACCEPTANCE_PATH).exists()


def scaffold_paths() -> tuple[PurePosixPath, ...]:
    return (PROJECT_ENTRY_PATH, PROJECT_ACCEPTANCE_PATH)


def test_init_writes_the_entry_and_the_acceptance_and_builds_ready(tmp_path: Path) -> None:
    project = tmp_path / "shop"

    result = _init(project)

    assert result.exit_code == 0, result.output
    assert sorted(path.relative_to(project).as_posix() for path in project.rglob("*") if path.is_file()) == [
        "acceptance/build.json",
        "datamimic.xml",
    ]
    assert "Wrote the flat project" in result.stdout
    assert result.stdout.splitlines()[-1] == NEXT_STEP_HINT
    built = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(built, ReadyBuild), built
    assert not built.coverage.has_gaps


def test_the_starter_sets_a_seed_and_an_expectation_so_that_no_gap_opens(tmp_path: Path) -> None:
    _init(tmp_path / "p")

    entry = (tmp_path / "p" / PROJECT_ENTRY_PATH).read_text(encoding="utf-8")
    acceptance = json.loads((tmp_path / "p" / PROJECT_ACCEPTANCE_PATH).read_text(encoding="utf-8"))
    assert "rngSeed=" in entry
    assert acceptance["version"] == "5.0"
    assert acceptance["expectations"]
    assert "max_count" not in acceptance


def test_init_is_ready_through_the_cli_with_exit_code_zero(tmp_path: Path) -> None:
    _init(tmp_path / "p")

    built = CliRunner().invoke(app, ["authoring", "build", str(tmp_path / "p")])

    assert built.exit_code == 0, built.output
    assert json.loads(built.stdout)["outcome"] == "ready"


def test_init_into_the_current_directory_style_path_creates_a_missing_directory(tmp_path: Path) -> None:
    result = _init(tmp_path / "a" / "b")

    assert result.exit_code == 0
    assert (tmp_path / "a" / "b" / PROJECT_ENTRY_PATH).is_file()


def test_init_refuses_an_existing_file_and_writes_nothing(tmp_path: Path) -> None:
    (tmp_path / PROJECT_ENTRY_PATH).write_text("mine", encoding="utf-8")

    result = _init(tmp_path)

    assert result.exit_code == 1
    assert "Init failed: these files exist already: datamimic.xml" in result.stderr
    assert (tmp_path / PROJECT_ENTRY_PATH).read_text(encoding="utf-8") == "mine"
    assert not (tmp_path / PROJECT_ACCEPTANCE_PATH).exists()


def test_init_refuses_a_symlinked_project_directory(tmp_path: Path, require_symlinks: None) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)

    result = _init(link)

    assert result.exit_code == 1
    assert "symlink" in result.stderr
    assert list(real.iterdir()) == []


def test_init_refuses_a_symlinked_target_inside_the_project(tmp_path: Path, require_symlinks: None) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    project = tmp_path / "p"
    project.mkdir()
    (project / "acceptance").symlink_to(outside, target_is_directory=True)

    result = _init(project)

    assert result.exit_code == 1
    assert "acceptance is a symlink; nothing written" in result.stderr
    assert list(outside.iterdir()) == []
    assert not (project / PROJECT_ENTRY_PATH).exists()


def test_init_refuses_a_file_as_project(tmp_path: Path) -> None:
    target = tmp_path / "file"
    target.write_text("x", encoding="utf-8")

    result = _init(target)

    assert result.exit_code == 1
    assert "PROJECT is a file" in result.stderr


def test_init_has_one_pattern_and_names_it_in_the_help() -> None:
    result = CliRunner().invoke(app, ["authoring", "init", "--help"])

    assert [item.value for item in ProjectPattern] == ["flat"]
    assert "flat" in result.stdout
    assert "Never overwrites" in result.stdout


def test_the_scaffold_acceptance_leaves_out_its_defaults(tmp_path: Path) -> None:
    scaffold = create_authoring_application(tmp_path).scaffold(ProjectPattern.FLAT)

    assert isinstance(scaffold, ProjectScaffold)
    paths = [file.path for file in scaffold.files]
    assert paths == [PurePosixPath("datamimic.xml"), PurePosixPath("acceptance/build.json")]
    payload = json.loads(scaffold.files[1].content)
    assert set(payload) == {"version", "expectations"}


@pytest.mark.parametrize("existing", ["datamimic.xml", "acceptance/build.json"])
def test_each_existing_file_blocks_the_whole_write(tmp_path: Path, existing: str) -> None:
    (tmp_path / existing).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / existing).write_text("mine", encoding="utf-8")
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file())

    with pytest.raises(FileExistsError, match=existing):
        write_project_scaffold(tmp_path, create_authoring_application(tmp_path).scaffold(ProjectPattern.FLAT))

    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*") if path.is_file()) == before


@pytest.mark.parametrize("existing", ["datamimic.xml", "acceptance/build.json"])
def test_init_does_not_overwrite_a_file_created_after_the_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: str
) -> None:
    check = workspace.check_project_scaffold

    def competing_write(*args, **kwargs):
        targets = check(*args, **kwargs)
        path = tmp_path / existing
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("other client", encoding="utf-8")
        return targets

    monkeypatch.setattr(workspace, "check_project_scaffold", competing_write)
    result = _init(tmp_path)

    assert result.exit_code == 1
    assert (tmp_path / existing).read_text(encoding="utf-8") == "other client"
    if existing == "acceptance/build.json":
        assert (tmp_path / PROJECT_ENTRY_PATH).is_file()
        assert "files already written: datamimic.xml" in result.stderr
        assert "Not written:" not in result.stderr


def test_explicit_overwrite_still_replaces_an_existing_file(tmp_path: Path) -> None:
    (tmp_path / PROJECT_ENTRY_PATH).write_text("old", encoding="utf-8")
    scaffold = create_authoring_application(tmp_path).scaffold(ProjectPattern.FLAT)

    write_project_scaffold(tmp_path, scaffold, overwrite=True)

    assert (tmp_path / PROJECT_ENTRY_PATH).read_text(encoding="utf-8") == scaffold.files[0].content


def test_runtime_project_helper_keeps_its_default_overwrite_behavior(tmp_path: Path) -> None:
    (tmp_path / PROJECT_ENTRY_PATH).write_text("old", encoding="utf-8")

    create_project_structure(tmp_path)

    assert (tmp_path / PROJECT_ENTRY_PATH).read_text(encoding="utf-8") != "old"


@pytest.mark.parametrize("force", [False, True])
def test_runtime_init_only_overwrites_a_competing_file_with_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, force: bool
) -> None:
    check = workspace.check_project_scaffold
    project = tmp_path / "shop"

    def competing_write(*args, **kwargs):
        targets = check(*args, **kwargs)
        project.mkdir(parents=True, exist_ok=True)
        (project / PROJECT_ENTRY_PATH).write_text("other client", encoding="utf-8")
        return targets

    monkeypatch.setattr(workspace, "check_project_scaffold", competing_write)
    args = ["init", "shop", "--target", str(tmp_path)]
    if force:
        args.append("--force")
    result = CliRunner().invoke(app, args)

    assert result.exit_code == (0 if force else 1)
    content = (project / PROJECT_ENTRY_PATH).read_text(encoding="utf-8")
    assert (content != "other client") if force else (content == "other client")
