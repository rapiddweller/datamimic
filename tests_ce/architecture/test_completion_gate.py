"""Completion requires current evidence and explicit review of every UNKNOWN."""

import json
from copy import deepcopy

import pytest

from tests_ce.architecture.completion_gate import check_completion, digest


def packet():
    frame = {
        "status": "UNKNOWN",
        "rules": {"U1": ["kind", "UNKNOWN"], "P1": ["kind", "PASS"]},
        "violations": {},
        "gaps": [{"kind": "external_type", "subject": "G1", "reason": "not proven"}],
        "contract_digest": "contract",
    }
    validation = {
        "outcome": "verdict",
        "status": "UNKNOWN",
        "exit_code": 2,
        "frame": deepcopy(frame),
        "baseline": {
            "state": "current", "exit_code": 2, "new": [], "gone": [],
            "accepted_entries": 2, "accepted_unknowns": 2, "accepted_rules": ["G1", "U1"],
        },
    }
    known = {"schema_version": "1.4.0", "budgets": {"calls_unresolved": 3}, "violations": []}
    review = {
        "reviewed_by": "reviewer",
        "contract_digest": "contract",
        "known_violations_digest": digest(known),
        "expected": {
            "pass": 1, "unknown": 1, "fail": 0, "gaps": 1, "accepted_entries": 2,
            "accepted_unknowns": 2, "gaps_digest": digest(frame["gaps"]),
        },
    }
    return validation, frame, review, known


def test_reviewed_unknown_retains_exit_two_and_evidence():
    validation, report, review, known = packet()
    original = deepcopy(validation)
    assert check_completion(validation, report, review, known) == 1
    assert validation == original


@pytest.mark.parametrize(
    "change",
    [
        "validation_refusal", "report_refusal", "outcome", "missing_frame", "stale_report", "rule_fail",
        "invalid_rule", "violation", "baseline_new", "baseline_gone", "baseline_state", "baseline_exit",
        "unknown_exit_zero", "unknown_exit_one", "status_pass", "gaps_missing", "gap_unaccepted",
        "rule_unaccepted", "underaccepted", "review_missing", "review_contract", "frame_contract",
        "new_unknown", "changed_gap", "review_count", "baseline_missing", "bad_accepted",
    ],
)
def test_hard_checks_and_negative_controls(change):
    validation, report, review, known = packet()
    frame = validation["frame"]
    baseline = validation["baseline"]
    if change == "validation_refusal":
        validation["refusal"] = {"kind": "invalid"}
    elif change == "report_refusal":
        report["refusal"] = {"kind": "invalid"}
    elif change == "outcome":
        validation["outcome"] = "command_refused"
    elif change == "missing_frame":
        del validation["frame"]
    elif change == "stale_report":
        report["rules"]["P1"][1] = "UNKNOWN"
    elif change in ("rule_fail", "invalid_rule"):
        frame["rules"]["U1"][1] = report["rules"]["U1"][1] = "FAIL" if change == "rule_fail" else "OTHER"
    elif change == "violation":
        frame["violations"]["V1"] = report["violations"]["V1"] = {}
    elif change in ("baseline_new", "baseline_gone"):
        baseline[change.removeprefix("baseline_")] = ["changed"]
    elif change == "baseline_state":
        baseline["state"] = "stale"
    elif change == "baseline_exit":
        baseline["exit_code"] = 1
    elif change in ("unknown_exit_zero", "unknown_exit_one"):
        validation["exit_code"] = 0 if change == "unknown_exit_zero" else 1
    elif change == "status_pass":
        validation["status"] = "PASS"
    elif change == "gaps_missing":
        frame["gaps"] = report["gaps"] = None
    elif change == "gap_unaccepted":
        baseline["accepted_rules"].remove("G1")
    elif change == "rule_unaccepted":
        baseline["accepted_rules"].remove("U1")
    elif change == "underaccepted":
        baseline["accepted_unknowns"] = 0
    elif change == "review_missing":
        review["reviewed_by"] = ""
    elif change == "review_contract":
        review["contract_digest"] = "stale"
    elif change == "frame_contract":
        report["contract_digest"] = "stale"
    elif change == "new_unknown":
        frame["gaps"].append({"kind": "other", "subject": "G2", "reason": "unknown"})
        report["gaps"] = deepcopy(frame["gaps"])
        baseline["accepted_rules"].append("G2")
    elif change == "changed_gap":
        frame["gaps"][0]["reason"] = report["gaps"][0]["reason"] = "different"
    elif change == "review_count":
        review["expected"]["unknown"] += 1
    elif change == "baseline_missing":
        del validation["baseline"]
    else:
        baseline["accepted_rules"] = None
    with pytest.raises(ValueError):
        check_completion(validation, report, review, known)


@pytest.mark.parametrize("change", ["raised_budget", "added_baseline_entry"])
def test_known_violations_change_needs_a_new_review(change):
    validation, report, review, known = packet()
    if change == "raised_budget":
        known["budgets"]["calls_unresolved"] += 1
    else:
        known["violations"].append({"id": "V1"})
    with pytest.raises(ValueError, match="known-violations.json changed"):
        check_completion(validation, report, review, known)


def test_whitespace_only_reformatting_of_known_violations_passes():
    validation, report, review, known = packet()
    assert check_completion(validation, report, review, json.loads(json.dumps(known, indent=4))) == 1


def test_clean_pass_requires_exit_zero():
    validation, report, review, known = packet()
    for frame in (validation["frame"], report):
        frame.update(status="PASS", rules={"P1": ["kind", "PASS"]}, gaps=[])
    validation.update(status="PASS", exit_code=0)
    validation["baseline"].update(exit_code=0, accepted_unknowns=0, accepted_rules=[])
    review["expected"].update(unknown=0, gaps=0, accepted_unknowns=0, gaps_digest=digest([]))
    assert check_completion(validation, report, review, known) == 0
