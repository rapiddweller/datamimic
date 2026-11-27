# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def copy_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[Path], Path]:
    """Copy the inputs and isolate SQLite paths, which resolve from the working directory."""

    def copy(source: Path) -> Path:
        project = shutil.copytree(
            source, tmp_path / source.name, ignore=shutil.ignore_patterns("output", "db", "__pycache__")
        )
        monkeypatch.chdir(project)
        return project

    return copy


@pytest.fixture
def project_dir(request: pytest.FixtureRequest, copy_project: Callable[[Path], Path]) -> Path:
    return copy_project(request.path.parent)
