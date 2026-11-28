# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Write a one-entry project and Build it, the way an agent does: files first, then Build the directory."""

from hashlib import sha256
from pathlib import Path

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.diagnostics import Diagnostic, DiagnosticPhase
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ACCEPTANCE_PATH,
    PROJECT_ENTRY_PATH,
    BuildRequestV5,
    BuildResult,
)
from datamimic_ce.errors.codes import IssueCode


def build_document(*, seed: int | None = 7, count: int = 2, exporter: bool = True) -> DmJsonDocumentV1:
    """The one-entry model shared by unit and integration Build proofs."""
    properties = {"name": "items", "count": count}
    if exporter:
        properties["target"] = "JSON"
    return DmJsonDocumentV1.model_validate(
        {
            "root": {
                "kind": "setup",
                "properties": {"rng_seed": seed} if seed is not None else {},
                "children": [
                    {
                        "kind": "generate",
                        "properties": properties,
                        "children": [
                            {"kind": "key", "properties": {"name": "id", "generator": "IncrementGenerator"}},
                        ],
                    },
                ],
            }
        }
    )


def write_project(root: Path, entry: DmJsonDocumentV1 | str, **acceptance: object) -> Path:
    """``entry`` is the datamimic.xml text, or a DM JSON document compiled to it; ``acceptance`` holds the
    BuildRequestV5 fields written to acceptance/build.json."""
    xml = entry if isinstance(entry, str) else CeDmJsonCodec().compile(entry).xml
    # newline="\n": Build digests file bytes, so a Windows text-mode write (CRLF) must not change what the test proves.
    (root / PROJECT_ENTRY_PATH).write_text(xml, encoding="utf-8", newline="\n")
    path = root / PROJECT_ACCEPTANCE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(BuildRequestV5.model_validate(acceptance).model_dump_json(), encoding="utf-8", newline="\n")
    return root


def build_project(root: Path, entry: DmJsonDocumentV1 | str, **acceptance: object) -> BuildResult:
    write_project(root, entry, **acceptance)
    return create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).build()


def entry_digest(root: Path) -> str:
    """Hash the exact persisted project entry used by a Build proof."""
    return sha256((root / PROJECT_ENTRY_PATH).read_bytes()).hexdigest()


def matches_scenario_diagnostic(item: Diagnostic, diagnostic: str, issue: str | None = None) -> bool:
    """Read scenario cases written before catalog codes replaced phase-local diagnostic codes."""
    if issue is not None:
        return item.code == issue
    match diagnostic:
        case "assert_failed":
            return item.code is IssueCode.TASK_ASSERT_FAILED
        case "child_execution":
            return item.code == "child_execution" or (
                isinstance(item.code, IssueCode) and item.phase is DiagnosticPhase.EVIDENCE and item.severity == "error"
            )
        case "descriptor":
            return item.code == "descriptor" or (
                isinstance(item.code, IssueCode) and item.phase is DiagnosticPhase.XML and item.rule is None
            )
        case _:
            return diagnostic in (item.rule, item.code)
