# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Shared projects and artifact inspection for assert-gate proofs."""

import json
import shutil
from pathlib import Path

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, ReadyBuild, ReadyWithGapsBuild, RejectedBuild

PROJECT = Path(__file__).resolve().parent / "scenarios" / "s21_assert_gate"
_NEGATIVES = {item["name"]: item["patch"] for item in json.loads((PROJECT / "scenario.json").read_text())["negatives"]}


def copy_project(tmp_path: Path, negative: str | None) -> Path:
    project = tmp_path / "project"
    shutil.copytree(PROJECT, project, ignore=shutil.ignore_patterns("scenario.json"))
    if negative is not None:
        patch = _NEGATIVES[negative]
        target = project / patch["file"]
        target.write_text(target.read_text(encoding="utf-8").replace(patch["old"], patch["new"]), encoding="utf-8")
    return project


def build_negative(tmp_path: Path, negative: str) -> RejectedBuild:
    result = create_authoring_application(copy_project(tmp_path, negative), descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(result, RejectedBuild)
    return result


def artifact_files(result: ReadyBuild | ReadyWithGapsBuild | RejectedBuild) -> dict[str, str]:
    artifact = result.review_artifact if isinstance(result, RejectedBuild) else result.artifact
    assert artifact is not None
    return {item.path.as_posix(): item.sha256 for item in artifact.files}
