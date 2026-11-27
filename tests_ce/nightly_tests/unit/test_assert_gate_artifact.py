# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Bound stopped-run evidence to the exact files read."""

from hashlib import sha256
from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, ReadyBuild, ReadyWithGapsBuild, RejectedBuild
from tests_ce.assert_gate_fixtures import artifact_files, build_negative, copy_project


@pytest.mark.parametrize("negative", ["fails_at_middle_row", "condition_raises"])
def test_the_review_artifact_binds_the_files_the_stopped_run_read(tmp_path: Path, negative: str) -> None:
    ready = create_authoring_application(
        copy_project(tmp_path / "ready", None), descriptor_path=PROJECT_ENTRY_PATH
    ).build()
    assert isinstance(ready, (ReadyBuild, ReadyWithGapsBuild))
    first = build_negative(tmp_path / "first", negative)
    project = copy_project(tmp_path / "second", negative)
    items = project / "data" / "entity" / "items.json"
    # A byte that no assert or check reads: the run stops at the same row with the same diagnostics.
    items.write_text(items.read_text(encoding="utf-8").replace('"S1"', '"S9"'), encoding="utf-8")
    second = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(second, RejectedBuild)

    assert [item.model_dump() for item in second.diagnostics] == [item.model_dump() for item in first.diagnostics]
    assert set(artifact_files(first)) == set(artifact_files(ready))
    assert artifact_files(second)["data/entity/items.json"] == sha256(items.read_bytes()).hexdigest()
    assert artifact_files(first)["data/entity/items.json"] != artifact_files(second)["data/entity/items.json"]
