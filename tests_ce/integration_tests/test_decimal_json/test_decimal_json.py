from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_TEST_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_DIR.parents[2]
_MODEL = _TEST_DIR / "model.dm.json"
_XML = _TEST_DIR / "datamimic.xml"


def _run_cli(*args: str, cwd: Path) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.cli", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": str(_REPO_ROOT)},
    )
    return json.loads(result.stdout)


def test_cli_scaffold_and_runtime_json_preserve_decimal_value(tmp_path: Path) -> None:
    scaffold = _run_cli("scaffold", str(_MODEL), "--format", "json", "--smoke-export", cwd=_TEST_DIR)
    assert scaffold["verified"] is True
    assert _XML.read_text(encoding="utf-8").removesuffix("\n") == scaffold["xml"]
    captured = scaffold["products"][0]["sample"][0]
    assert captured["amount"] == "0.1"
    assert type(captured["amount"]) is str
    acceptance = scaffold["acceptance"]["results"]
    amount_acceptance = next(item for item in acceptance if item.get("field") == "amount")
    assert amount_acceptance["status"] == "pass"
    assert amount_acceptance["observed_minimum"] == "0.1"
    assert amount_acceptance["observed_maximum"] == "0.1"

    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(_XML.read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(
        [sys.executable, "-m", "datamimic_ce.cli", "run", str(descriptor)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=os.environ | {"PYTHONPATH": str(_REPO_ROOT)},
    )
    output = json.loads((tmp_path / "output" / "out" / "decimal_rows.json").read_text(encoding="utf-8"))
    assert output == [{"amount": "0.1", "sequence": 7}]
    assert type(output[0]["amount"]) is str
    assert type(output[0]["sequence"]) is int
