"""Reject completion without current, reviewed ArchKeel 5.0 evidence."""

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_completion(validation: dict, report: dict, review: dict, known_violations: dict) -> int:
    if validation.get("refusal") or report.get("refusal") or validation.get("outcome") != "verdict":
        raise ValueError("Architecture validation or report was refused.")
    frame = validation.get("frame")
    if not isinstance(frame, dict) or not isinstance(report, dict):
        raise ValueError("Architecture frames are missing.")
    for key in ("status", "rules", "violations", "gaps", "contract_digest"):
        if key not in frame or frame[key] != report.get(key):
            raise ValueError("Validation and report evidence does not match.")
    rules, gaps, violations = frame["rules"], frame["gaps"], frame["violations"]
    if not isinstance(rules, dict) or not isinstance(gaps, list) or not isinstance(violations, dict):
        raise ValueError("Invalid architecture frame.")
    if violations or any(
        not isinstance(rule, list) or len(rule) != 2 or rule[1] not in ("PASS", "UNKNOWN")
        for rule in rules.values()
    ):
        raise ValueError("Architecture violations or failed rules remain.")
    counts = Counter(rule[1] for rule in rules.values())
    status = "UNKNOWN" if counts["UNKNOWN"] or gaps else "PASS"
    exit_code = 2 if status == "UNKNOWN" else 0
    if (validation.get("status"), validation.get("exit_code"), frame["status"]) != (status, exit_code, status):
        raise ValueError("Architecture status and exit code are inconsistent.")
    baseline = validation.get("baseline")
    if not isinstance(baseline, dict) or (
        baseline.get("state") != "current"
        or baseline.get("exit_code") != exit_code
        or baseline.get("new") != []
        or baseline.get("gone") != []
    ):
        raise ValueError("Architecture baseline is stale or has drift.")
    accepted = baseline.get("accepted_rules")
    accepted_unknowns = baseline.get("accepted_unknowns")
    accepted_entries = baseline.get("accepted_entries")
    if (
        not isinstance(accepted, list)
        or any(not isinstance(item, str) for item in accepted)
        or type(accepted_unknowns) is not int
        or type(accepted_entries) is not int
        or accepted_entries < 0
        or accepted_unknowns < len(gaps)
        or any(not isinstance(gap, dict) or not isinstance(gap.get("subject"), str) for gap in gaps)
    ):
        raise ValueError("Accepted UNKNOWN coverage is invalid.")
    subjects = {gap["subject"] for gap in gaps}
    unknown_rules = {name for name, rule in rules.items() if rule[1] == "UNKNOWN"}
    if not (subjects | unknown_rules) <= set(accepted) or accepted_unknowns < len(subjects | unknown_rules):
        raise ValueError("Accepted UNKNOWNs do not cover the frame.")
    if review.get("known_violations_digest") != digest(known_violations):
        raise ValueError("known-violations.json changed after review.")
    reviewer = review.get("reviewed_by")
    if (
        not isinstance(reviewer, str)
        or not reviewer.strip()
        or not isinstance(frame["contract_digest"], str)
        or not frame["contract_digest"]
        or review.get("contract_digest") != frame["contract_digest"]
    ):
        raise ValueError("Independent review is missing or does not match the contract.")
    expected = {
        "pass": counts["PASS"],
        "unknown": counts["UNKNOWN"],
        "fail": counts["FAIL"],
        "gaps": len(gaps),
        "accepted_unknowns": accepted_unknowns,
        "accepted_entries": baseline.get("accepted_entries"),
        "gaps_digest": digest(gaps),
    }
    if review.get("expected") != expected:
        raise ValueError("Review evidence does not match the current UNKNOWNs.")
    return len(gaps)


if __name__ == "__main__":
    try:
        validation, report, review, known = (
            json.loads(Path(path).read_text(encoding="utf-8")) for path in sys.argv[1:]
        )
        count = check_completion(validation, report, review, known)
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(str(error)) from error
    print(f"Architecture completion: {validation['status']}; 0 violations; {count} reviewed UNKNOWN gaps.")
