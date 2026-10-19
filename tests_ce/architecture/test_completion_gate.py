"""Completion requires current evidence and explicit review of every UNKNOWN."""

from copy import deepcopy

import pytest

from tests_ce.architecture.completion_gate import check_completion, digest


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
        "reviewed_by": "Astra", "source_digest": "source", "contract_digest": "contract",
        "analyzer_digest": "analyzer", "unknowns_digest": digest(records),
        "validation_digest": digest(validation),
        "groups": [{"classification": "external_type", "reason": "Static evidence cannot prove the external provider.", "ids": ["U1"]}],
    }
    return validation, report, review


def test_assessed_unknown_is_retained_and_accepted():
    validation, report, review = packet()
    original = deepcopy(report)
    assert check_completion(validation, report, review) == 1
    assert report == original


@pytest.mark.parametrize("change", ["violation", "coverage", "filter", "new", "changed", "source", "contract", "analyzer", "unreviewed", "duplicate", "missing"])
def test_completion_rejects_incomplete_or_unreviewed_evidence(change):
    validation, report, review = packet()
    if change == "violation":
        report["filtered_violations"] = [{"id": "V1"}]
    elif change == "coverage":
        report["coverage"]["status"] = "UNKNOWN"
    elif change == "filter":
        report["report_filter"]["component"] = "COMP-IO"
    elif change == "new":
        report["recorded_unknowns"].append({"id": "U2", "evidence_class": "UNKNOWN"})
    elif change == "changed":
        report["recorded_unknowns"][0]["data"]["reason"] = "missing_annotation"
    elif change in {"source", "contract", "analyzer"}:
        review[change + "_digest"] = "stale"
    elif change == "unreviewed":
        review["groups"][0]["ids"] = []
    elif change == "duplicate":
        review["groups"][0]["ids"].append("U1")
    else:
        report["recorded_unknowns"] = None
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
    review["validation_digest"] = digest(validation)
    return validation, report, review


def test_reviewed_validation_uncertainty_preserves_raw_exit_and_diagnostic():
    validation, report, review = publication_packet()
    original = deepcopy(validation)
    assert check_completion(validation, report, review) == 1
    assert validation == original


@pytest.mark.parametrize("change", ["unreviewed", "unused", "claim", "pointer", "unexpected_exit", "empty", "stale_payload"])
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
    elif change == "empty":
        validation["diagnostics"] = []
        review["validation_unknowns"]["diagnostics"] = []
    else:
        validation["claims"] = {"unread_bindings": 1}
    if change != "stale_payload":
        review["validation_digest"] = digest(validation)
    with pytest.raises(ValueError):
        check_completion(validation, report, review)


@pytest.mark.parametrize("source", ["validation", "report"])
def test_reviewed_usage_uncertainty_cannot_hide_measurement_failure(source):
    validation, report, review = publication_packet()
    result = validation if source == "validation" else report
    result["failures"] = ["measurement budget exceeded in calls_unresolved: 1278->1395"]
    review["validation_digest"] = digest(validation)
    with pytest.raises(ValueError, match="failures remain"):
        check_completion(validation, report, review)
