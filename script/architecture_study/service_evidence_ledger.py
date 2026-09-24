"""Emit a per-path ledger for service-classified descriptor comparisons."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from script.architecture_study.service_inventory import REPO, build_report

FROZEN = "a219163e533d661bcc7bda0faa5ecc77909ab5aa"
TARGET_CODE_XML_CONTROL = "658f3a5f588a8df44bee1b8395e186ea760be4cc"
CLASSES = {"exact_seeded", "normalized_unseeded", "normalized_error"}
STEP22 = "docs/architecture/refactoring-study/experiment-2/step-08c22.md"
STEP24 = "docs/architecture/refactoring-study/experiment-2/step-08c24.md"
VERIFICATION = "docs/architecture/refactoring-study/experiment-2/verification-2026-09-23.md"
STEP27 = "docs/architecture/refactoring-study/experiment-2/step-08c27.md"
STEP28 = "docs/architecture/refactoring-study/experiment-2/step-08c28.md"
STEP30 = "docs/architecture/refactoring-study/experiment-2/step-08c30.md"

# Only per-path statements in the step records are promoted. Batch membership
# and aggregate totals do not establish an individual comparison class.
EVIDENCE = {
    "tests_ce/integration_tests/test_composite_reference/composite_exhausted.xml": (
        "normalized_error", STEP22
    ),
    "tests_ce/integration_tests/test_reference_distribution/ref_ordered_exhausted.xml": (
        "normalized_error", STEP22
    ),
    "tests_ce/integration_tests/test_reference_distribution/ref_unique_cyclic_invalid.xml": (
        "normalized_error", STEP22
    ),
    "tests_ce/integration_tests/test_sql_crud_targets/sql_update_no_pk.xml": (
        "normalized_error", STEP22
    ),
    "tests_ce/integration_tests/test_execute_script/execute_script_and_body.xml": (
        "normalized_error", STEP22
    ),
    "tests_ce/integration_tests/test_execute_script/execute_script_and_uri.xml": (
        "normalized_error", STEP22
    ),
    "tests_ce/integration_tests/test_iterate_offset/test_offset_client_rejected.xml": (
        "normalized_error", STEP22
    ),
    "tests_ce/integration_tests/test_execute_script/execute_script_non_string.xml": (
        "normalized_error", STEP22
    ),
    "tests_ce/integration_tests/test_page_process/test_page_process_sqlite.xml": (
        "normalized_unseeded", STEP24
    ),
    "tests_ce/integration_tests/test_source_read_determinism/sqlite_seeded.xml": (
        "exact_seeded", VERIFICATION
    ),
    "tests_ce/external_service_tests/test_rdbms/test_postgresql_local.xml": (
        "normalized_unseeded", STEP27
    ),
    "tests_ce/external_service_tests/test_mongodb/test_mongodb_pagination_happy.xml": (
        "normalized_unseeded", STEP28
    ),
    "tests_ce/external_service_tests/test_mongodb/test_mongodb_pagination_edge.xml": (
        "normalized_unseeded", STEP30
    ),
    "tests_ce/external_service_tests/test_mongodb/test_mongodb_decimal.xml": (
        "exact_seeded", STEP30
    ),
}


def validate_evidence_reference(reference: str) -> None:
    path = PurePosixPath(reference)
    prefix = ("docs", "architecture", "refactoring-study", "experiment-2")
    if (
        not reference.strip()
        or path.is_absolute()
        or ".." in path.parts
        or path.parts[:4] != prefix
        or len(path.parts) < 5
        or not (REPO / Path(*path.parts)).is_file()
    ):
        raise ValueError(f"invalid experiment-2 evidence reference: {reference!r}")


def build_ledger(
    inventory_paths: list[str],
    evidence_rows: dict[str, tuple[str, str]] | None = None,
) -> dict[str, Any]:
    evidence_rows = EVIDENCE if evidence_rows is None else evidence_rows
    if len(inventory_paths) != len(set(inventory_paths)):
        raise ValueError("service inventory contains duplicate paths")
    universe = set(inventory_paths)
    unknown = set(evidence_rows) - universe
    if unknown:
        raise ValueError(f"evidence paths are not in service inventory: {sorted(unknown)}")

    entries = []
    for path in sorted(universe):
        evidence = evidence_rows.get(path)
        evidence_class, reference = evidence if evidence else (None, None)
        if evidence is not None:
            if evidence_class not in CLASSES:
                raise ValueError(f"invalid evidence class for {path}: {evidence_class}")
            validate_evidence_reference(reference)
        entries.append(
            {
                "path": path,
                "status": evidence_class or "UNVERIFIED",
                "evidence_ref": reference,
            }
        )

    counts = Counter(entry["status"] for entry in entries)
    return {
        "frozen_revision": FROZEN,
        "target_code_xml_control_revision": TARGET_CODE_XML_CONTROL,
        "inventory_source": "script/architecture_study/service_inventory.py",
        "service_path_count": len(entries),
        "counts": dict(sorted(counts.items())),
        "entries": entries,
    }


def self_check() -> None:
    ledger = build_ledger(["a.xml", "b.xml"], {})
    assert ledger["service_path_count"] == 2
    assert ledger["counts"] == {"UNVERIFIED": 2}
    try:
        build_ledger(["a.xml", "a.xml"], {})
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate inventory paths must fail")
    try:
        build_ledger(["a.xml"], {"b.xml": ("exact_seeded", STEP22)})
    except ValueError:
        pass
    else:
        raise AssertionError("evidence outside the inventory must fail")
    try:
        build_ledger(["a.xml"], {"a.xml": ("unknown", STEP22)})
    except ValueError:
        pass
    else:
        raise AssertionError("unknown evidence classes must fail")
    for reference in ("", "/tmp/evidence.md", "docs/../outside.md", f"{STEP22}.missing"):
        try:
            validate_evidence_reference(reference)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"invalid evidence reference must fail: {reference!r}")
    for row in (("exact_seeded", ""), ("exact_seeded",)):
        try:
            build_ledger(["a.xml"], {"a.xml": row})
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("missing evidence references must fail")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
    inventory = build_report()
    ledger = build_ledger([entry["path"] for entry in inventory["entries"]])
    print(json.dumps(ledger, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
