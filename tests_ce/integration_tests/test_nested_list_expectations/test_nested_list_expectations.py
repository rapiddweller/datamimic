from __future__ import annotations

import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from pydantic import TypeAdapter

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.expectations import (
    AllowedValuesExpectation,
    ExactCountExpectation,
    ExpectationIntent,
    ProductRowsSubject,
    RangeExpectation,
    UniqueExpectation,
)
from datamimic_ce.authoring.domain.proof import (
    AcceptanceRequirement,
    BuildVerificationOptions,
    VerificationGateStatus,
)
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ENTRY_PATH,
    BuildResult,
    DecompileDocumentRequest,
    ReadyBuild,
    ReadyDecompileDocument,
    RejectedBuild,
)
from tests_ce.authoring_project import write_project

_TEST_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_DIR.parents[2]
_XML = _TEST_DIR / "datamimic.xml"
_EMPTY_XML = _TEST_DIR / "empty-nested-list.xml"
_REQUIREMENTS = TypeAdapter(tuple[AcceptanceRequirement, ...])
_BUILD_RESULT = TypeAdapter(BuildResult)


def _project(
    tmp_path: Path,
    *,
    xml: Path = _XML,
    expectations: tuple[ExpectationIntent, ...] = (),
    requirements: Path | None = None,
) -> Path:
    application = create_authoring_application(workspace_root=_TEST_DIR)
    decoded = application.decompile_document(DecompileDocumentRequest(xml=xml.read_text()))
    assert isinstance(decoded, ReadyDecompileDocument), decoded
    return write_project(
        tmp_path,
        decoded.document,
        expectations=expectations,
        acceptance_requirements=_REQUIREMENTS.validate_json(requirements.read_text()) if requirements else (),
        verification=BuildVerificationOptions(smoke_export=True),
    )


def _run_cli(project: Path) -> BuildResult:
    process = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", "authoring", "build", str(project)],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
        env=os.environ | {"PYTHONPATH": str(_REPO_ROOT)},
    )
    assert process.stderr == ""
    result = _BUILD_RESULT.validate_json(process.stdout)
    assert process.returncode == (0 if isinstance(result, ReadyBuild) else 1), process.stdout
    return result


def _expectations(*, failing: bool = False) -> tuple[ExpectationIntent, ...]:
    subject = ProductRowsSubject(product="orders", list_field="items")
    return (
        ExactCountExpectation(subject=subject, count=3 if failing else 4),
        UniqueExpectation(subject=subject, field="line_no", scope="global" if failing else "per_parent"),
        RangeExpectation(
            subject=subject,
            field="amount",
            minimum=Decimal(100 if failing else 10),
            maximum=Decimal(200 if failing else 20),
        ),
        AllowedValuesExpectation(
            subject=subject, field="status", values=("pending",) if failing else ("open", "closed")
        ),
    )


def test_build_verifies_nested_list_expectations_and_xml_roundtrip(tmp_path: Path) -> None:
    result = _run_cli(_project(tmp_path, expectations=_expectations()))
    assert isinstance(result, ReadyBuild), result
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED
    rows = result.evidence[0].rows
    assert result.evidence[0].count == len(rows) == 2
    items = [item for row in rows for item in row["items"]]
    assert len(items) == 4
    for row in rows:
        assert len({item["line_no"] for item in row["items"]}) == len(row["items"])
    assert all(10 <= item["amount"] <= 20 and item["status"] in {"open", "closed"} for item in items)
    decoded = create_authoring_application(workspace_root=tmp_path).decompile_document(
        DecompileDocumentRequest(xml=_XML.read_text())
    )
    assert isinstance(decoded, ReadyDecompileDocument)
    files = {item.path: item.sha256 for item in result.artifact.files}
    assert files[PROJECT_ENTRY_PATH] == decoded.canonical_xml_sha256


def test_bad_nested_list_subjects_reject_with_new_transaction_paths(tmp_path: Path) -> None:
    for subject, field, suffix in (
        (ProductRowsSubject(product="orders", list_field="missing_items"), "amount", ("subject", "list_field")),
        (ProductRowsSubject(product="orders", list_field="items"), "missing_amount", ("field",)),
    ):
        expectation = RangeExpectation(subject=subject, field=field, minimum=Decimal(0), maximum=Decimal(1))
        _project(tmp_path, expectations=(expectation,))
        result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()
        assert isinstance(result, RejectedBuild)
        assert result.phase.value == "expectation"
        assert result.diagnostics[0].path == ("expectations", 0, *suffix)


def test_nested_list_all_four_requirement_families_fail_on_bad_rows(tmp_path: Path) -> None:
    result = _run_cli(_project(tmp_path, expectations=_expectations(failing=True)))
    assert isinstance(result, RejectedBuild)
    failures = [item for item in result.diagnostics if item.path[:1] == ("expectations",)]
    assert {item.code.value for item in failures} == {"exact_count", "unique", "range", "allowed_values"}
    assert len(failures) == 4


def test_caller_nested_list_requirement_accepts_empty_list(tmp_path: Path) -> None:
    result = _run_cli(_project(tmp_path, xml=_EMPTY_XML, requirements=_TEST_DIR / "caller-valid-empty.json"))
    assert isinstance(result, ReadyBuild), result
    assert result.evidence[0].rows == ({"order_id": 1, "items": []},)
    assert not result.diagnostics


def test_caller_nested_list_unknown_references_reject_even_for_empty_rows(tmp_path: Path) -> None:
    for filename, suffix in (
        ("caller-invalid-inner-field.json", ("field",)),
        ("caller-invalid-list-field.json", ("subject", "list_field")),
    ):
        result = _run_cli(_project(tmp_path, xml=_EMPTY_XML, requirements=_TEST_DIR / filename))
        assert isinstance(result, RejectedBuild)
        assert result.phase.value == "expectation"
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].path == ("acceptance_requirements", 0, "expectation", *suffix)
