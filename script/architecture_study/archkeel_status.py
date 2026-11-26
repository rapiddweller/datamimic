# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
"""Create a Shields endpoint from a native ArchKeel validation receipt."""

import argparse
import json
from collections import Counter
from pathlib import Path

REPORT_URL = "https://rapiddweller.github.io/datamimic/"


def make_status(validation: dict) -> dict:
    frame = validation["frame"]
    rules = frame["rules"]
    violations = frame["violations"]
    if not isinstance(rules, dict) or not isinstance(violations, (dict, list)):
        raise ValueError("Invalid ArchKeel frame")
    counts = Counter()
    for rule in rules.values():
        if not isinstance(rule, list) or len(rule) != 2 or rule[1] not in ("PASS", "UNKNOWN", "FAIL"):
            raise ValueError("Invalid ArchKeel rule")
        counts[rule[1]] += 1
    status = validation["status"]
    exit_code = validation["exit_code"]
    baseline_state = validation["baseline"]["state"]
    if status not in ("PASS", "UNKNOWN", "FAIL") or exit_code not in (0, 1, 2):
        raise ValueError("Invalid ArchKeel verdict")
    failed = counts["FAIL"] or len(violations) or status == "FAIL" or exit_code == 1
    unknown = counts["UNKNOWN"] or status == "UNKNOWN" or exit_code == 2
    return {
        "schemaVersion": 1,
        "label": "ArchKeel",
        "message": f'{counts["PASS"]} pass · {counts["UNKNOWN"]} unknown · {counts["FAIL"]} fail',
        "color": "red" if failed else "orange" if unknown else "green",
        "status": status,
        "exitCode": exit_code,
        "pass": counts["PASS"],
        "unknown": counts["UNKNOWN"],
        "fail": counts["FAIL"],
        "violations": len(violations),
        "baselineState": baseline_state,
        "reportUrl": REPORT_URL,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("validation", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = make_status(json.loads(args.validation.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
