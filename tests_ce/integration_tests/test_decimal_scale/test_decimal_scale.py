from __future__ import annotations

import json
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from datamimic_ce.authoring.contracts import (
    AuthoringStage,
    IntentValidationIssueCode,
    ScaffoldRequest,
    ScaffoldVerification,
    VerificationGateStatus,
)
from datamimic_ce.authoring.service import compile_document, scaffold
from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run() -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory() as temporary_directory:
        descriptor_dir = Path(temporary_directory)
        (descriptor_dir / "decimal_scale.xml").write_text(
            (_TEST_DIR / "decimal_scale.xml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        engine = DataMimicTest(descriptor_dir, "decimal_scale.xml", capture_test_result=True)
        engine.test_with_timer()
        return engine.capture_result()["payments"]


def test_decimal_scale_compiles_to_runtime_grid_and_replays() -> None:
    model = json.loads((_TEST_DIR / "model.dm.json").read_text(encoding="utf-8"))
    compiled = compile_document(model)
    expected_xml = (_TEST_DIR / "decimal_scale.xml").read_text(encoding="utf-8").strip()
    assert compiled.xml == expected_xml

    scaffolded = scaffold(
        ScaffoldRequest(
            spec=model,
            max_count=25,
            verification=ScaffoldVerification(deterministic_replay=True),
        )
    )
    assert scaffolded.xml == expected_xml
    assert scaffolded.verified
    assert scaffolded.verification.deterministic_replay.status is VerificationGateStatus.PASSED

    first = _run()
    second = _run()
    assert first == second
    for row in first:
        amount = row["amount"]
        assert isinstance(amount, Decimal)
        assert Decimal("1.001") <= amount <= Decimal("9.019")
        assert amount == amount.quantize(Decimal("0.01"))
        assert amount.as_tuple().exponent == -2

        whole_amount = row["whole_amount"]
        assert isinstance(whole_amount, Decimal)
        assert Decimal("2.1") <= whole_amount <= Decimal("4.9")
        assert whole_amount == whole_amount.quantize(Decimal("1"))
        assert whole_amount.as_tuple().exponent == 0

        fine_amount = row["fine_amount"]
        assert isinstance(fine_amount, Decimal)
        assert Decimal("0.000000000000001") <= fine_amount <= Decimal("0.000000000000009")
        assert fine_amount == fine_amount.quantize(Decimal("0.000000000000001"))
        assert fine_amount.as_tuple().exponent == -15

        large_amount = row["large_amount"]
        assert isinstance(large_amount, Decimal)
        assert Decimal("1000000000000000") <= large_amount <= Decimal("1000000000000009")
        assert large_amount.as_tuple().exponent == -15


@pytest.mark.parametrize(
    ("filename", "path"),
    [
        ("invalid_scale.dm.json", ("products", 0, "fields", 0, "scale")),
        ("invalid_grid.dm.json", ("products", 0, "fields", 0)),
    ],
)
def test_invalid_decimal_scale_intent_descriptors_fail_at_model_boundary(
    filename: str,
    path: tuple[str | int, ...],
) -> None:
    spec = json.loads((_TEST_DIR / filename).read_text(encoding="utf-8"))
    result = scaffold(ScaffoldRequest(spec=spec))
    assert result.ok is False
    assert result.stage is AuthoringStage.RENDER
    assert result.verified is False
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.code is IntentValidationIssueCode.CONSTRAINT_VIOLATION
    assert issue.path == path
