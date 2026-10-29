# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A nestedKey list whose variable source ends stops with the last full element, as a generate stops with its last
full row (#450). The scenario tests_ce/scenarios/s35_nested_key_source_ends holds the project and the variants."""

import json
import shutil
from pathlib import Path

import pytest

from datamimic_ce.authoring.domain.requests import RejectedBuild
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
from tests_ce.authoring_project import build_project

_DIR = Path(__file__).resolve().parent
_SCENARIO = _DIR.parents[1] / "scenarios" / "s35_nested_key_source_ends"
_NEGATIVES = [item["name"] for item in json.loads((_SCENARIO / "scenario.json").read_text())["negatives"]]


def _run(directory: Path, filename: str) -> dict:
    engine = DataMimicTest(test_dir=directory, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


@pytest.mark.parametrize("negative", _NEGATIVES)
def test_a_list_that_its_source_ends_holds_no_empty_element(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, negative: str
) -> None:
    project = shutil.copytree(_SCENARIO, tmp_path / "project")
    [patch] = [
        item["patch"]
        for item in json.loads((project / "scenario.json").read_text())["negatives"]
        if item["name"] == negative
    ]
    target = project / patch["file"]
    target.write_text(target.read_text(encoding="utf-8").replace(patch["old"], patch["new"]), encoding="utf-8")
    monkeypatch.chdir(project)

    baskets = _run(project, "datamimic.xml")["baskets"]

    assert [[item.get("fruit") for item in basket["items"]] for basket in baskets] == [["apple", "pear"]] * 2


def test_a_source_backed_list_keeps_the_elements_before_the_end(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(_DIR)

    [basket] = _run(_DIR, "nested_key_source_path.xml")["baskets"]

    assert basket["items"] == [{"slot": "1", "name": "Ada"}]


def test_a_list_in_a_condition_that_ends_early_leaves_the_capture_unknown(tmp_path: Path) -> None:
    # The acceptance projection does not see a list inside <condition>, so only the capture can carry the signal.
    shutil.copytree(_DIR / "data", tmp_path / "data")
    result = build_project(
        tmp_path,
        (_DIR / "nested_key_in_condition.xml").read_text(encoding="utf-8"),
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "baskets"}, "count": 2}],
    )

    assert isinstance(result, RejectedBuild)
    assert [
        (str(item.code), "a <nestedKey> list ended before its count" in item.message) for item in result.diagnostics
    ] == [("validation", True)]
