# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A non-cyclic variable source that ends drops the parent row; the child rows made for that row go with it (#451).
The scenario tests_ce/scenarios/s34_source_end_drops_children holds the project and the variant."""

import json
import shutil
from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent
_SCENARIO = _DIR.parents[1] / "scenarios" / "s34_source_end_drops_children"


def _run(directory: Path, filename: str) -> dict:
    engine = DataMimicTest(test_dir=directory, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


def test_a_dropped_parent_keeps_no_child_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = shutil.copytree(_SCENARIO, tmp_path / "project")
    [negative] = json.loads((project / "scenario.json").read_text())["negatives"]
    patch = negative["patch"]
    target = project / patch["file"]
    target.write_text(target.read_text(encoding="utf-8").replace(patch["old"], patch["new"]), encoding="utf-8")
    monkeypatch.chdir(project)

    captured = _run(project, "datamimic.xml")

    assert [row["order_id"] for row in captured["orders"]] == [1, 2]
    assert [row["order_id"] for row in captured["lines"]] == [1, 1, 2, 2]


def test_a_memstore_readback_holds_no_child_row_of_a_dropped_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_DIR)

    captured = _run(_DIR, "memstore_readback.xml")

    assert sorted(row["order_id"] for row in captured["line_copy"]) == [1, 1, 2, 2]
