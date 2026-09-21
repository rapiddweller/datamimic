from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from datamimic_ce.authoring.contracts import (
    AcceptanceStatus,
    AllowedValuesAcceptanceResult,
    ExactCountAcceptanceResult,
    RangeAcceptanceResult,
    ScaffoldRequest,
    ScaffoldResult,
    UniqueAcceptanceResult,
)
from datamimic_ce.authoring.service import scaffold

_TEST_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_DIR.parents[2]
_MODEL = _TEST_DIR / "model.dm.json"
_XML = _TEST_DIR / "datamimic.xml"
_ACCEPTANCE_FAILURE = _TEST_DIR / "acceptance-fail.dm.json"


def _run_cli(*args: str, expect_success: bool = True) -> ScaffoldResult:
    result = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.cli", *args],
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": str(_REPO_ROOT)},
    )
    if expect_success:
        assert result.returncode == 0
    else:
        assert result.returncode != 0
    return ScaffoldResult.model_validate_json(result.stdout)


def test_scaffold_verifies_nested_list_expectations_and_generated_xml() -> None:
    result = _run_cli("scaffold", str(_MODEL), "--format", "json", "--smoke-export")

    assert result.verified is True
    assert _XML.read_text(encoding="utf-8").removesuffix("\n") == result.xml
    assert result.acceptance is not None
    results = result.acceptance.results
    assert sum(isinstance(item, ExactCountAcceptanceResult) for item in results) == 2
    assert sum(isinstance(item, UniqueAcceptanceResult) for item in results) == 1
    assert sum(isinstance(item, RangeAcceptanceResult) for item in results) == 1
    assert sum(isinstance(item, AllowedValuesAcceptanceResult) for item in results) == 1
    nested_count = next(
        item
        for item in results
        if isinstance(item, ExactCountAcceptanceResult) and item.list_field == "items"
    )
    assert nested_count.observed_count == 4
    assert all(item.status is AcceptanceStatus.PASS for item in results)


def test_bad_nested_list_subjects_fail_at_spec_validation() -> None:
    for filename, expected in (
        ("invalid-list-field.dm.json", "unknown nested_list field"),
        ("invalid-inner-field.dm.json", "unknown field 'missing_amount'"),
    ):
        spec = json.loads((_TEST_DIR / filename).read_text(encoding="utf-8"))
        result = scaffold(ScaffoldRequest(spec=spec, max_count=10, sample_rows=5))

        assert result.ok is False
        assert result.issues
        assert expected in result.issues[0].message


def test_nested_list_expectations_fail_on_bad_rows() -> None:
    result = _run_cli(
        "scaffold",
        str(_ACCEPTANCE_FAILURE),
        "--format",
        "json",
        "--smoke-export",
        expect_success=False,
    )

    assert result.verified is False
    assert result.acceptance is not None
    failed = {
        type(item)
        for item in result.acceptance.results
        if item.status is AcceptanceStatus.FAIL
    }
    assert failed == {
        ExactCountAcceptanceResult,
        UniqueAcceptanceResult,
        RangeAcceptanceResult,
        AllowedValuesAcceptanceResult,
    }
    assert result.acceptance.failed == 4
