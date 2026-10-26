"""Reject architecture completion without a current independent UNKNOWN review."""

import hashlib
import json
import sys
from pathlib import Path


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_completion(validation: dict, report: dict, review: dict, known_violations: dict) -> int:
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
    # Budgets and accepted baseline entries are decisions; a change needs a measurement_amendment and a new digest.
    if review.get("known_violations_digest") != digest(known_violations):
        raise ValueError("known-violations.json changed after independent review.")
    diagnostics = validation.get("diagnostics") or []
    assessment = review.get("validation_unknowns") or {}
    if diagnostics:
        if not (
            validation.get("exit_code") == 2
            and all(item.get("code") == "interface.usage_unknown" for item in diagnostics)
            and assessment.get("classification") and assessment.get("reason")
            and assessment.get("diagnostics") == diagnostics
        ):
            raise ValueError("Validation diagnostics are not independently assessed uncertainty.")
    elif validation.get("exit_code") != 0 or assessment:
        raise ValueError("Validation exit or review does not match its diagnostics.")
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
    projection = report["architecture_projection"]
    # Source and validation digests are not bound: they change with every edit and prove no review.
    identities = {
        "contract_digest": projection["contract_digest"],
        "analyzer_digest": projection["analyzer_digest"],
    }
    if review.get("reviewed_by") != "Astra" or any(
        not value or review.get(key) != value for key, value in identities.items()
    ):
        raise ValueError("Independent review does not match the current Target and analyzer.")
    records = report.get("recorded_unknowns")
    if not isinstance(records, list) or any(record.get("evidence_class") != "UNKNOWN" for record in records):
        raise ValueError("Complete UNKNOWN records are unavailable.")
    groups = review.get("groups") or []
    if any(not group.get("classification") or not group.get("reason") for group in groups):
        raise ValueError("Every UNKNOWN group needs an explicit assessment.")
    assessed = [identity for group in groups for identity in group["ids"]]
    if len(set(assessed)) != len(assessed) or sorted(assessed) != sorted(record["id"] for record in records):
        raise ValueError("Every UNKNOWN must be independently assessed exactly once.")
    return len(records)


if __name__ == "__main__":
    try:
        count = check_completion(*(json.loads(Path(path).read_text()) for path in sys.argv[1:]))
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise SystemExit(str(error)) from error
    print(f"Architecture completion: 0 violations; {count} assessed UNKNOWN records remain.")
