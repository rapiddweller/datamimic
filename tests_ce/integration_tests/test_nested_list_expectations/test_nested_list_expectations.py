from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from datamimic_ce.authoring.contracts import AcceptanceStatus, ScaffoldRequest
from datamimic_ce.authoring.service import scaffold

_TEST_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_DIR.parents[2]
_MODEL = _TEST_DIR / "model.dm.json"
_XML = _TEST_DIR / "datamimic.xml"


def _run_cli(*args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.cli", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": str(_REPO_ROOT)},
    )
    return json.loads(result.stdout)


def test_scaffold_verifies_nested_list_expectations_and_generated_xml() -> None:
    result = _run_cli("scaffold", str(_MODEL), "--format", "json", "--smoke-export")

    assert result["verified"] is True
    assert _XML.read_text(encoding="utf-8").removesuffix("\n") == result["xml"]
    results = result["acceptance"]["results"]
    assert {(item["kind"], item.get("list_field")) for item in results} == {
        ("exact_count", None),
        ("exact_count", "items"),
        ("unique", "items"),
        ("range", "items"),
        ("allowed_values", "items"),
    }
    nested_count = next(item for item in results if item.get("list_field") == "items" and item["kind"] == "exact_count")
    assert nested_count["observed_count"] == 4
    assert all(item["status"] == "pass" for item in results)


def test_bad_nested_list_subjects_fail_at_spec_validation() -> None:
    for filename, expected in (
        ("invalid-list-field.dm.json", "unknown nested_list field"),
        ("invalid-inner-field.dm.json", "unknown field 'missing_amount'"),
    ):
        spec = json.loads((_TEST_DIR / filename).read_text(encoding="utf-8"))
        result = scaffold(ScaffoldRequest(spec=spec))

        assert result.ok is False
        assert result.issues
        assert expected in result.issues[0].message


def test_nested_list_expectations_fail_on_bad_rows() -> None:
    model = json.loads(_MODEL.read_text(encoding="utf-8"))
    model["expectations"] = [
        {"kind": "exact_count", "product": "orders", "list_field": "items", "count": 3},
        {
            "kind": "unique",
            "product": "orders",
            "list_field": "items",
            "field": "line_no",
            "scope": "global",
        },
        {
            "kind": "range",
            "product": "orders",
            "list_field": "items",
            "field": "amount",
            "minimum": 100,
            "maximum": 200,
        },
        {
            "kind": "allowed_values",
            "product": "orders",
            "list_field": "items",
            "field": "status",
            "values": ["pending"],
        },
    ]

    result = scaffold(ScaffoldRequest(spec=model))

    failed = {item.kind for item in result.acceptance.results if item.status is AcceptanceStatus.FAIL}
    assert failed == {"exact_count", "unique", "range", "allowed_values"}
    assert result.verified is False
