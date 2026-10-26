"""Completion requires current evidence and explicit review of every UNKNOWN."""

from copy import deepcopy

import pytest

from tests_ce.architecture.completion_gate import check_completion


def packet():
    validation = {
        "exit_code": 0, "observation_complete": "PASS", "declared_rules": "UNKNOWN",
        "coverage": {"status": "PASS"}, "baseline_new": 0, "baseline_resolved": 0,
        "measurements": {"scalars": {"violations": 0, "unknown_positions": 1}},
    }
    records = [{"id": "U1", "evidence_class": "UNKNOWN", "data": {"reason": "external_type"}}]
    report = {
        "schema_version": "2.0.0", "exit_code": 0, "observation_complete": "PASS",
        "declared_rules": "UNKNOWN", "coverage": {"status": "PASS"}, "diagnostics": [],
        "report_filter": {"only_architecture": True, "full_architecture": True, "component": None, "rule": None},
        "filtered_violations": [], "recorded_unknowns": records,
        "architecture_projection": {"source": {"source_digest": "source"}, "contract_digest": "contract", "analyzer_digest": "analyzer"},
    }
    review = {
        "reviewed_by": "Astra", "contract_digest": "contract",
        "analyzer_digest": "analyzer",
        "groups": [{"classification": "external_type", "reason": "Static evidence cannot prove the external provider.", "ids": ["U1"]}],
    }
    return validation, report, review


def test_assessed_unknown_is_retained_and_accepted():
    validation, report, review = packet()
    original = deepcopy(report)
    assert check_completion(validation, report, review) == 1
    assert report == original


def test_source_validation_and_record_churn_needs_no_rebind():
    validation, report, review = packet()
    report["architecture_projection"]["source"]["source_digest"] = "edited"
    validation["measurements"]["scalars"]["unknown_positions"] = 2
    validation["coverage"]["calls_analyzed"] = 99
    report["recorded_unknowns"][0].update(fact_id="F2", evidence_id="E2")
    assert check_completion(validation, report, review) == 1


HARD_CHECKS = [
    "violation", "baseline_new", "baseline_resolved", "violation_scalar", "validation_failure", "report_failure",
    "coverage", "observation", "rules", "report_exit", "report_diagnostic", "schema", "filter",
    "filtered_violation", "not_unknown_class", "records_missing", "validation_exit",
]


@pytest.mark.parametrize("change", HARD_CHECKS)
def test_hard_checks_still_fail(change):
    validation, report, review = packet()
    if change == "violation":
        report["filtered_violations"] = [{"id": "V1"}]
    elif change in {"baseline_new", "baseline_resolved"}:
        validation[change] = 1
    elif change == "violation_scalar":
        validation["measurements"]["scalars"]["violations"] = 1
    elif change == "validation_failure":
        validation["failures"] = ["budget exceeded"]
    elif change == "report_failure":
        report["failures"] = ["budget exceeded"]
    elif change == "coverage":
        report["coverage"]["status"] = "UNKNOWN"
    elif change == "observation":
        validation["observation_complete"] = "UNKNOWN"
    elif change == "rules":
        validation["declared_rules"] = "FAIL"
    elif change == "report_exit":
        report["exit_code"] = 1
    elif change == "report_diagnostic":
        report["diagnostics"] = [{"code": "x"}]
    elif change == "schema":
        report["schema_version"] = "1.0.0"
    elif change == "filter":
        report["report_filter"]["component"] = "COMP-IO"
    elif change == "filtered_violation":
        report["filtered_violations"] = [{"id": "V1"}]
    elif change == "not_unknown_class":
        report["recorded_unknowns"][0]["evidence_class"] = "PROVEN"
    elif change == "records_missing":
        report["recorded_unknowns"] = None
    else:
        validation["exit_code"] = 2
    with pytest.raises(ValueError):
        check_completion(validation, report, review)


@pytest.mark.parametrize("change", ["contract", "analyzer", "reviewer"])
def test_review_target_and_analyzer_must_match(change):
    validation, report, review = packet()
    review["reviewed_by" if change == "reviewer" else change + "_digest"] = "stale"
    with pytest.raises(ValueError, match="does not match"):
        check_completion(validation, report, review)


GROUP_BREAKS = ["new_unknown", "extra_group_id", "unreviewed", "duplicate", "no_reason", "no_classification"]


@pytest.mark.parametrize("change", GROUP_BREAKS)
def test_every_unknown_needs_exactly_one_assessment(change):
    validation, report, review = packet()
    group = review["groups"][0]
    if change == "new_unknown":
        report["recorded_unknowns"].append({"id": "U2", "evidence_class": "UNKNOWN"})
    elif change == "extra_group_id":
        group["ids"].append("U9")
    elif change == "unreviewed":
        group["ids"] = []
    elif change == "duplicate":
        group["ids"].append("U1")
    elif change == "no_reason":
        group["reason"] = ""
    else:
        del group["classification"]
    with pytest.raises(ValueError):
        check_completion(validation, report, review)


def publication_packet():
    validation, report, review = packet()
    diagnostic = {
        "code": "interface.usage_unknown", "kind": "contract_invalid",
        "pointer": "/components/0/public/0", "subject": "sample.models:Model",
        "unknown_claim": "Inherited publication is not proven.", "remedy": "Resolve the inherited signature.",
    }
    validation.update(exit_code=2, diagnostics=[diagnostic])
    review["validation_unknowns"] = {
        "classification": "inherited_publication_usage_unproved",
        "reason": "The registered service returns the model through an unresolved inherited type variable.",
        "diagnostics": deepcopy(validation["diagnostics"]),
    }
    return validation, report, review


def test_reviewed_validation_uncertainty_preserves_raw_exit_and_diagnostic():
    validation, report, review = publication_packet()
    original = deepcopy(validation)
    assert check_completion(validation, report, review) == 1
    assert validation == original


@pytest.mark.parametrize("change", ["unreviewed", "unused", "claim", "pointer", "unexpected_exit", "empty"])
def test_validation_uncertainty_cannot_bypass_completion(change):
    validation, report, review = publication_packet()
    if change == "unreviewed":
        del review["validation_unknowns"]
    elif change == "unused":
        validation["diagnostics"][0]["code"] = "interface.unused"
        review["validation_unknowns"]["diagnostics"] = deepcopy(validation["diagnostics"])
    elif change in {"claim", "pointer"}:
        key = "unknown_claim" if change == "claim" else "pointer"
        validation["diagnostics"][0][key] = "changed"
    elif change == "unexpected_exit":
        validation["exit_code"] = 1
    else:
        validation["diagnostics"] = []
        review["validation_unknowns"]["diagnostics"] = []
    with pytest.raises(ValueError):
        check_completion(validation, report, review)


@pytest.mark.parametrize("source", ["validation", "report"])
def test_reviewed_usage_uncertainty_cannot_hide_measurement_failure(source):
    validation, report, review = publication_packet()
    result = validation if source == "validation" else report
    result["failures"] = ["measurement budget exceeded in calls_unresolved: 1278->1395"]
    with pytest.raises(ValueError, match="failures remain"):
        check_completion(validation, report, review)
