from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from datamimic_ce.authoring.contracts import AcceptanceStatus, RangeAcceptanceResult, ScaffoldResult

_TEST_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_DIR.parents[2]
_MODEL = _TEST_DIR / "model.dm.json"
_XML = _TEST_DIR / "datamimic.xml"
_EDGE_XML = _TEST_DIR / "edge_cases.xml"


def _run_cli(*args: str, cwd: Path) -> ScaffoldResult:
    result = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.cli", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": str(_REPO_ROOT)},
    )
    return ScaffoldResult.model_validate_json(result.stdout)


def _run_descriptor(xml: Path, tmp_path: Path, output_name: str) -> Path:
    descriptor = tmp_path / xml.name
    descriptor.write_text(xml.read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(
        [sys.executable, "-m", "datamimic_ce.cli", "run", str(descriptor)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": str(_REPO_ROOT)},
    )
    return tmp_path / "output" / "out" / output_name


def test_cli_scaffold_and_runtime_json_preserve_decimal_value(tmp_path: Path) -> None:
    scaffold = _run_cli("scaffold", str(_MODEL), "--format", "json", "--smoke-export", cwd=_TEST_DIR)
    assert scaffold.verified is True
    assert _XML.read_text(encoding="utf-8").removesuffix("\n") == scaffold.xml
    captured = scaffold.products[0].sample[0]
    assert captured["amount"] == "0.1"
    assert type(captured["amount"]) is str
    assert scaffold.acceptance is not None
    amount_acceptance = next(
        item
        for item in scaffold.acceptance.results
        if isinstance(item, RangeAcceptanceResult) and item.field == "amount"
    )
    assert amount_acceptance.status is AcceptanceStatus.PASS
    assert amount_acceptance.observed_minimum == "0.1"
    assert amount_acceptance.observed_maximum == "0.1"

    output_path = _run_descriptor(_XML, tmp_path, "decimal_rows.json")
    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert output == [{"amount": "0.1", "sequence": 7}]
    assert type(output[0]["amount"]) is str
    assert type(output[0]["sequence"]) is int


def test_raw_dsl_preserves_decimal_precision_and_scale_in_ndjson(tmp_path: Path) -> None:
    output_path = _run_descriptor(_EDGE_XML, tmp_path, "decimal_edges_0.ndjson")
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

    assert rows == [
        {
            "high_precision": "0.100000000000000005",
            "trailing_zero": "-123.4500",
            "zero": "0.00",
            "count": 7,
        }
    ]
    assert all(type(row[field]) is str for field in ("high_precision", "trailing_zero", "zero") for row in rows)
    assert type(rows[0]["count"]) is int
