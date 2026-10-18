from __future__ import annotations

import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from datamimic_ce.authoring.domain.expectations import (
    ExactCountExpectation,
    ProductRowsSubject,
    RangeExpectation,
)
from datamimic_ce.authoring.domain.proof import (
    BuildVerificationOptions,
    VerificationGateStatus,
)
from datamimic_ce.authoring.domain.requests import (
    BuildRequestV4,
    ReadyBuild,
    ReadyCompileDocument,
    ReadyDecompileDocument,
)

_TEST_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_DIR.parents[2]
_XML = _TEST_DIR / "datamimic.xml"
_EDGE_XML = _TEST_DIR / "edge_cases.xml"


def _run_cli(*args: str, cwd: Path, stdin: str | None = None) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", *args],
        cwd=cwd,
        input=stdin,
        timeout=60,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": str(_REPO_ROOT)},
    )
    assert result.stderr == ""
    return result.stdout


def _run_descriptor(xml: Path, tmp_path: Path, output_name: str) -> Path:
    descriptor = tmp_path / xml.name
    descriptor.write_text(xml.read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", "run", str(descriptor)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": str(_REPO_ROOT)},
    )
    return tmp_path / "output" / "out" / output_name


def test_cli_build_and_runtime_json_preserve_decimal_value(tmp_path: Path) -> None:
    decompiled = ReadyDecompileDocument.model_validate_json(_run_cli("authoring", "decompile", str(_XML), cwd=tmp_path))
    compiled = ReadyCompileDocument.model_validate_json(
        _run_cli("authoring", "compile", "-", cwd=tmp_path, stdin=decompiled.document.model_dump_json())
    )
    assert compiled.artifact.xml_sha256 == decompiled.canonical_xml_sha256
    subject = ProductRowsSubject(product="decimal_rows")
    request = BuildRequestV4(
        document=decompiled.document,
        expectations=(
            ExactCountExpectation(subject=subject, count=1),
            RangeExpectation(subject=subject, field="amount", minimum=Decimal("0.1"), maximum=Decimal("0.1")),
        ),
        verification=BuildVerificationOptions(smoke_export=True),
    )
    built = ReadyBuild.model_validate_json(
        _run_cli(
            "authoring",
            "build",
            "-",
            "--workspace-root",
            str(tmp_path),
            cwd=tmp_path,
            stdin=request.model_dump_json(exclude_none=True),
        )
    )
    assert built.artifact.xml_sha256 == compiled.artifact.xml_sha256
    assert built.verification.smoke_export.status is VerificationGateStatus.PASSED
    captured = built.evidence[0].rows[0]
    assert captured["amount"] == "0.1"
    assert type(captured["amount"]) is str
    assert built.evidence[0].count == 1
    assert not built.diagnostics

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
