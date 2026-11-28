# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
"""Report the native ArchKeel rule verdicts in CI and on GitHub Pages."""

import argparse
import json
from collections import Counter
from pathlib import Path

REPORT_URL = "https://rapiddweller.github.io/datamimic/"


def make_status(validation: dict) -> dict:
    if not isinstance(validation, dict) or validation.get("outcome") != "verdict":
        raise ValueError("ArchKeel did not return a verdict")
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
    if {"PASS": 0, "UNKNOWN": 2, "FAIL": 1}.get(status) != exit_code:
        raise ValueError("Invalid ArchKeel verdict")
    return {
        "schemaVersion": 1,
        "label": "ArchKeel",
        "message": f"{counts['PASS']} pass · {counts['UNKNOWN']} unknown · {counts['FAIL']} fail",
        "color": "red" if counts["FAIL"] else "yellow" if counts["UNKNOWN"] else "green",
        "status": status,
        "exitCode": exit_code,
        "pass": counts["PASS"],
        "unknown": counts["UNKNOWN"],
        "fail": counts["FAIL"],
        "violations": len(violations),
        "reportUrl": REPORT_URL,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("validation", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--gate", action="store_true")
    args = parser.parse_args()
    try:
        validation = json.loads(args.validation.read_text(encoding="utf-8"))
        result = make_status(validation)
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(f"Invalid ArchKeel validation ({args.validation}): {error}") from error
    if args.gate:
        print(f"ArchKeel: {result['message']}; diagnostics: {args.validation}")
        for name, (_, verdict) in validation["frame"]["rules"].items():
            if verdict == "FAIL":
                print(f"FAIL: {name}")
        raise SystemExit(1 if result["fail"] else 0)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
