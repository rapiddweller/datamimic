"""Reject architecture completion without a current independent UNKNOWN review."""

import hashlib
import json
import sys
from pathlib import Path


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_substance(validation: dict, report: dict) -> int:
    """Checks that need no review: the code and its evidence are clean."""
    for result in (validation, report):
        if result.get("failures"):
            raise ValueError("Architecture validation or report failures remain.")
        if not (
            result.get("observation_complete") == "PASS"
            and result.get("declared_rules") in {"PASS", "UNKNOWN"}
            and (result.get("coverage") or {}).get("status") == "PASS"
        ):
            raise ValueError("Architecture observation or validation is incomplete.")
    if report.get("exit_code") != 0 or report.get("diagnostics"):
        raise ValueError("Architecture report is incomplete.")
    diagnostics = validation.get("diagnostics") or []
    if diagnostics:
        if not (
            validation.get("exit_code") == 2
            and all(item.get("code") == "interface.usage_unknown" for item in diagnostics)
        ):
            raise ValueError("Validation diagnostics are not uncertainty.")
    elif validation.get("exit_code") != 0:
        raise ValueError("Validation exit does not match its diagnostics.")
    if validation["measurements"]["scalars"]["violations"] != 0 or any(
        validation.get(key) != 0 for key in ("baseline_new", "baseline_resolved")
    ):
        raise ValueError("Architecture violations or baseline drift remain.")
    selection = report.get("report_filter") or {}
    if not (
        report.get("schema_version") == "2.0.0" and selection.get("only_architecture") is True
        and selection.get("full_architecture") is True
        and selection.get("component") is None and selection.get("rule") is None
        and report.get("filtered_violations") == []
    ):
        raise ValueError("Completion requires the full unfiltered architecture report.")
    records = report.get("recorded_unknowns")
    if not isinstance(records, list) or any(record.get("evidence_class") != "UNKNOWN" for record in records):
        raise ValueError("Complete UNKNOWN records are unavailable.")
    return len(records)


def check_review_binding(validation: dict, report: dict, review: dict) -> None:
    """Checks that the recorded independent review matches the current evidence."""
    if review.get("validation_digest") != digest(validation):
        raise ValueError("Validation changed after independent review.")
    diagnostics = validation.get("diagnostics") or []
    assessment = review.get("validation_unknowns") or {}
    if diagnostics:
        if not (
            assessment.get("classification") and assessment.get("reason")
            and assessment.get("diagnostics") == diagnostics
        ):
            raise ValueError("Validation diagnostics are not independently assessed uncertainty.")
    elif assessment:
        raise ValueError("Validation exit or review does not match its diagnostics.")
    projection = report["architecture_projection"]
    identities = {
        "source_digest": projection["source"]["source_digest"],
        "contract_digest": projection["contract_digest"],
        "analyzer_digest": projection["analyzer_digest"],
    }
    if review.get("reviewed_by") != "Astra" or any(
        not value or review.get(key) != value for key, value in identities.items()
    ):
        raise ValueError("Independent review does not match the current Source, Target and analyzer.")
    records = report["recorded_unknowns"]
    if review.get("unknowns_digest") != digest(sorted(records, key=lambda record: record["id"])):
        raise ValueError("UNKNOWN records changed after independent review.")
    groups = review.get("groups") or []
    if any(not group.get("classification") or not group.get("reason") for group in groups):
        raise ValueError("Every UNKNOWN group needs an explicit assessment.")
    assessed = [identity for group in groups for identity in group["ids"]]
    if len(set(assessed)) != len(assessed) or sorted(assessed) != sorted(record["id"] for record in records):
        raise ValueError("Every UNKNOWN must be independently assessed exactly once.")


def check_completion(validation: dict, report: dict, review: dict) -> int:
    count = check_substance(validation, report)
    check_review_binding(validation, report, review)
    return count


if __name__ == "__main__":
    # Fork pull requests run the substance only: an outside contributor cannot record the review.
    substance_only = sys.argv[1:2] == ["--substance-only"]
    paths = sys.argv[2:] if substance_only else sys.argv[1:]
    try:
        if substance_only:
            count = check_substance(*(json.loads(Path(path).read_text()) for path in paths[:2]))
        else:
            count = check_completion(*(json.loads(Path(path).read_text()) for path in paths))
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(str(error)) from error
    if substance_only:
        print(f"Architecture completion (substance only): 0 violations; {count} UNKNOWN records not reviewed here.")
    else:
        print(f"Architecture completion: 0 violations; {count} assessed UNKNOWN records remain.")
