from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from datamimic_ce.authoring.contracts import (
    AcceptanceSource,
    AcceptanceStatus,
    AllowedValuesAcceptanceResult,
    ExactCountAcceptanceResult,
    IntentValidationIssueCode,
    RangeAcceptanceResult,
    ScaffoldRequest,
    ScaffoldResult,
    UniqueAcceptanceResult,
)
from datamimic_ce.authoring.application.service import scaffold

_TEST_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_DIR.parents[2]
_MODEL = _TEST_DIR / "model.dm.json"
_XML = _TEST_DIR / "datamimic.xml"
_ACCEPTANCE_FAILURE = _TEST_DIR / "acceptance-fail.dm.json"
_EMPTY_MODEL = _TEST_DIR / "empty-nested-list.dm.json"
_CALLER_VALID = _TEST_DIR / "caller-valid-empty.json"
_CALLER_INVALID_INNER = _TEST_DIR / "caller-invalid-inner-field.json"
_CALLER_INVALID_LIST = _TEST_DIR / "caller-invalid-list-field.json"


def _run_cli(*args: str, expect_success: bool = True) -> ScaffoldResult:
    result = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", *args],
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


def test_caller_nested_list_expectation_accepts_empty_list() -> None:
    result = _run_cli(
        "scaffold",
        str(_EMPTY_MODEL),
        "--acceptance-requirements",
        str(_CALLER_VALID),
        "--format",
        "json",
        "--smoke-export",
    )

    assert result.verified is True
    assert result.acceptance is not None
    caller = next(item for item in result.acceptance.results if item.source is AcceptanceSource.CALLER)
    assert isinstance(caller, ExactCountAcceptanceResult)
    assert caller.list_field == "items"
    assert caller.observed_count == 0
    assert caller.status is AcceptanceStatus.PASS


def test_caller_nested_list_references_fail_with_structured_paths() -> None:
    for requirements, expected_path, expected_message in (
        (
            _CALLER_INVALID_INNER,
            ("acceptance_requirements", 0, "field"),
            "unknown field 'missing_amount' in nested_list 'orders.items'",
        ),
        (
            _CALLER_INVALID_LIST,
            ("acceptance_requirements", 0, "list_field"),
            "unknown nested_list field 'orders.missing_items'",
        ),
    ):
        result = _run_cli(
            "scaffold",
            str(_EMPTY_MODEL),
            "--acceptance-requirements",
            str(requirements),
            "--format",
            "json",
            expect_success=False,
        )

        assert result.ok is False
        assert len(result.issues) == 1
        issue = result.issues[0]
        assert issue.path == expected_path
        assert issue.code is IntentValidationIssueCode.CONSTRAINT_VIOLATION
        assert expected_message in issue.message
