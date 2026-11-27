# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from fnmatch import fnmatch
from pathlib import Path

import pytest

from tests_ce.scenarios.test_scenarios import _DIRECTORIES, _assert_outcome, _build, _copy, _load, _run


@pytest.mark.parametrize("directory", _DIRECTORIES, ids=lambda path: path.name)
def test_scenario_builds_runs_and_replays(directory: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    scenario = _load(directory)
    project = _copy(directory, tmp_path / directory.name)
    monkeypatch.chdir(project)  # file and SQLite products resolve against the working directory

    built = _build(project)
    _assert_outcome(built, scenario)

    first = _run(project)
    counts = {name: len(rows) for name, rows in first.items() if name in scenario.products}
    assert counts == scenario.products
    assert _run(project) == first, "a second run with the same seed must give identical rows"
    if scenario.exports:
        exported = [path.relative_to(project).as_posix() for path in (project / "output").rglob("*") if path.is_file()]
        assert all(any(fnmatch(path, pattern) for path in exported) for pattern in scenario.exports), exported
    _assert_outcome(_build(project), scenario)  # what the runs exported must not change the Build outcome
