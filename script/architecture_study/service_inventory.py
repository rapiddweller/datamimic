"""List service-backed descriptors and nearby test references as candidates only."""

from __future__ import annotations

import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from script.architecture_study.verify_step0 import REPO, inventory

CLIENT_TAGS = {"database", "mongodb", "kafka", "object-storage"}
CLIENT_HINTS = {"id", "system", "environment", "dbms", "type"}


def client_hints(element: ET.Element) -> dict[str, str]:
    return {key: value for key, value in sorted(element.attrib.items()) if key in CLIENT_HINTS}


def candidate_status(paths: list[str]) -> str:
    if not paths:
        return "unresolved"
    if len(paths) > 1:
        return "ambiguous"
    return "single-candidate-not-proof"


def tracked_test_sources() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--", "tests_ce/**/*.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return [REPO / path for path in result.stdout.splitlines()]


def build_report(
    records: list[dict[str, Any]] | None = None,
    test_sources: list[Path] | None = None,
) -> dict[str, Any]:
    records = inventory() if records is None else records
    test_sources = tracked_test_sources() if test_sources is None else test_sources
    descriptors = [
        record
        for record in records
        if "external-service" in record["category"]
        and "non-descriptor" not in record["category"]
    ]
    entries = []
    for record in descriptors:
        descriptor = REPO / record["path"]
        root = ET.parse(descriptor).getroot()
        clients = [
            {
                "tag": element.tag.rsplit("}", 1)[-1].lower(),
                "declared_hints": client_hints(element),
            }
            for element in root.iter()
            if element.tag.rsplit("}", 1)[-1].lower() in CLIENT_TAGS
        ]
        candidates = sorted(
            source.relative_to(REPO).as_posix()
            for source in test_sources
            if descriptor.name in source.read_text(encoding="utf-8", errors="replace")
        )
        entries.append(
            {
                "path": record["path"],
                "clients": clients,
                "owner_candidates": candidates,
                "owner_candidate_status": candidate_status(candidates),
            }
        )
    return {
        "descriptor_count": len(entries),
        "execution_status": "not-assessed",
        "safety_status": "not-assessed",
        "owner_evidence": (
            "Exact basename mentions in tracked tests_ce Python test files; "
            "candidates only, not execution proof."
        ),
        "client_evidence": "Only declared type/profile hints; no resolved endpoint or credentials.",
        "entries": entries,
    }


def self_check(report: dict[str, Any]) -> None:
    assert report["descriptor_count"] == len(report["entries"])
    assert candidate_status([]) == "unresolved"
    assert candidate_status(["tests_ce/test_a.py", "tests_ce/test_b.py"]) == "ambiguous"
    assert candidate_status(["tests_ce/test_mentions_but_executes_another_file.py"]) == (
        "single-candidate-not-proof"
    )
    assert client_hints(ET.Element("database", {"system": "postgresql", "password": "secret"})) == {
        "system": "postgresql"
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    arguments = parser.parse_args()
    report = build_report()
    if arguments.self_check:
        self_check(report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
