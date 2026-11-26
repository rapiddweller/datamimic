# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

_TEST_DIR = Path(__file__).resolve().parent / "integration_tests/test_determinism_seed_scenarios"
_REPO_ROOT = _TEST_DIR.parents[2]
_RUN_IN_FRESH_PROCESS = """
import json, sys
from pathlib import Path
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
engine = DataMimicTest(test_dir=Path(sys.argv[1]), filename=sys.argv[2], capture_test_result=True)
engine.test_with_timer()
result = json.dumps(engine.capture_result(), default=str, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
print("RESULT" + result)
"""


def canonical_result_bytes(result: object) -> bytes:
    serialized = json.dumps(result, default=str, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return serialized.encode("utf-8")


def _run_in_fresh_process(filename: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-c", _RUN_IN_FRESH_PROCESS, str(_TEST_DIR), filename],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        cwd=_REPO_ROOT,
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONPATH": str(_REPO_ROOT),
            "PYTHONUTF8": "1",
        },
    )
    result_line = next(line for line in completed.stdout.splitlines() if line.startswith("RESULT"))
    parsed: object = json.loads(result_line.removeprefix("RESULT"))
    if not isinstance(parsed, dict):
        raise ValueError("fresh process result must be a JSON object")
    result: dict[str, object] = {}
    for key, value in parsed.items():
        if not isinstance(key, str):
            raise ValueError("fresh process result keys must be strings")
        result[key] = value
    return result


def seeded_model_hash(filename: str) -> str:
    return hashlib.sha256(canonical_result_bytes(_run_in_fresh_process(filename))).hexdigest()
