# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A failed <assert> keeps the Build proof of the products made before it (#420). The project and its variants are
tests_ce/scenarios/s21_assert_gate; the scenario runner checks one code per variant. This module checks the facts
that one code cannot carry: what Build kept, what it could not evaluate, and that no property value reaches it."""

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RejectedBuild
from datamimic_ce.interfaces.cli import app

_PROJECT = Path(__file__).resolve().parents[2] / "scenarios" / "s21_assert_gate"
_NEGATIVES = {item["name"]: item["patch"] for item in json.loads((_PROJECT / "scenario.json").read_text())["negatives"]}


def _copy(tmp_path: Path, negative: str | None) -> Path:
    project = tmp_path / "project"
    shutil.copytree(_PROJECT, project)
    if negative is not None:  # the scenario.json patch is the single source of the variant
        patch = _NEGATIVES[negative]
        target = project / patch["file"]
        target.write_text(target.read_text(encoding="utf-8").replace(patch["old"], patch["new"]), encoding="utf-8")
    return project


def _build(tmp_path: Path, negative: str) -> RejectedBuild:
    result = create_authoring_application(_copy(tmp_path, negative), descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(result, RejectedBuild)
    return result


def _codes(result: RejectedBuild) -> list[str]:
    return [str(item.code) for item in result.diagnostics if item.severity == "error"]


def _not_evaluated(result: RejectedBuild) -> set[str]:
    [item] = [item for item in result.diagnostics if str(item.code) == "not_executed"]
    assert isinstance(item.expected, list)
    return {json.dumps(path) for path in item.expected}


@pytest.mark.parametrize("negative", ["fails_at_first_row", "fails_at_middle_row", "fails_at_last_row"])
def test_the_failed_row_does_not_change_what_build_keeps(tmp_path: Path, negative: str) -> None:
    result = _build(tmp_path, negative)
    first_row = _build(tmp_path / "first", "fails_at_first_row")

    assert [item.model_dump() for item in result.diagnostics] == [item.model_dump() for item in first_row.diagnostics]
    assert _codes(result) == ["assert_failed", "not_executed"]
    assert [product.name for product in result.evidence] == ["items"]
    assert "Declared product capture is missing." not in result.model_dump_json()
    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.path == ("descriptor", "datamimic.xml", "assert", "line", 11)
    assert failed.message == "The <assert> in 'lines' failed: A line holds at most 4 items"


def test_an_included_step_keeps_every_product_before_it(tmp_path: Path) -> None:
    result = _build(tmp_path, "fails_in_included_step")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.path == ("include", "model/stock.xml", "assert", "line", 4)
    assert [product.name for product in result.evidence] == ["items", "lines", "parts"]
    # Only the two checks on the stock product stay unevaluated; the checks on the earlier products passed.
    assert len(_not_evaluated(result)) == 2
    assert _codes(result) == ["assert_failed", "not_executed"]


def test_a_nested_assert_names_its_generate_and_loses_the_whole_outer_product(tmp_path: Path) -> None:
    result = _build(tmp_path, "fails_in_nested_generate")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.path == ("descriptor", "datamimic.xml", "assert", "line", 16)
    assert "in 'parts'" in failed.message
    assert [product.name for product in result.evidence] == ["items"]


def test_an_assert_after_every_product_leaves_nothing_unevaluated(tmp_path: Path) -> None:
    result = _build(tmp_path, "fails_after_all_products")

    assert _codes(result) == ["assert_failed"]
    assert [product.name for product in result.evidence] == ["items", "lines", "parts", "stock"]


def test_an_unrelated_failing_expectation_is_still_reported(tmp_path: Path) -> None:
    result = _build(tmp_path, "assert_and_failing_expectation")

    assert _codes(result) == ["assert_failed", "range", "not_executed"]


def test_two_failing_asserts_report_the_first_in_run_order(tmp_path: Path) -> None:
    result = _build(tmp_path, "two_asserts_fail")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.expected == "A line holds at most 4 items"


@pytest.mark.parametrize("negative", ["message_is_a_property", "message_has_braces", "message_has_dunder"])
def test_a_message_that_can_hold_a_value_is_not_shown(tmp_path: Path, negative: str) -> None:
    result = _build(tmp_path, negative)

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.expected is None
    assert "is not shown" in failed.message
    serialized = result.model_dump_json()
    # A normal run resolves {audit_note} to this value (scenario.json run_error); Build must not show it.
    assert "TOPSECRET-21" not in serialized
    assert "{audit_note}" not in serialized and "__qty__" not in serialized


def test_an_assert_without_message_says_so(tmp_path: Path) -> None:
    result = _build(tmp_path, "assert_without_message")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.expected is None
    assert "has no message" in failed.message


def test_a_condition_that_raises_stays_a_broken_expression(tmp_path: Path) -> None:
    result = _build(tmp_path, "condition_raises")

    assert _codes(result) == ["child_execution"]
    assert result.evidence == ()


@pytest.mark.parametrize(("negative", "exit_code"), [(None, 0), ("fails_at_last_row", 1)])
def test_datamimic_run_stops_with_exit_one_only_when_an_assert_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, negative: str | None, exit_code: int
) -> None:
    monkeypatch.chdir(_copy(tmp_path, negative))

    assert CliRunner().invoke(app, ["run", "datamimic.xml"]).exit_code == exit_code


def test_an_assert_in_the_first_product_still_lists_every_check_it_could_not_evaluate(tmp_path: Path) -> None:
    # S12 r4_above_maximum: the assert guards the first product, so the run stops before any capture.
    s12 = _PROJECT.parent / "s12_personnel_approvals"
    [patch] = [
        item["patch"]
        for item in json.loads((s12 / "scenario.json").read_text())["negatives"]
        if item["name"] == "r4_above_maximum"
    ]
    project = tmp_path / "s12"
    shutil.copytree(s12, project)
    target = project / patch["file"]
    target.write_text(target.read_text(encoding="utf-8").replace(patch["old"], patch["new"]), encoding="utf-8")

    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, RejectedBuild)
    assert _codes(result) == ["assert_failed", "not_executed"]
    assert result.evidence == ()
    assert len(_not_evaluated(result)) == 72
