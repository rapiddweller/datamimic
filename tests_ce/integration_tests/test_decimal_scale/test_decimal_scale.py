from __future__ import annotations

import json
import tempfile
from decimal import Decimal
from pathlib import Path

from datamimic_ce.authoring.contracts import ScaffoldRequest, ScaffoldVerification, VerificationGateStatus
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
        assert Decimal("1.001") <= amount <= Decimal("1.019")
        assert amount == amount.quantize(Decimal("0.01"))
        assert amount.as_tuple().exponent == -2
