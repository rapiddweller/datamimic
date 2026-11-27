# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build gates that need an unmodified runtime, exporter, replay, or file scan."""

from pathlib import Path

import pytest

from datamimic_ce.authoring.domain.capture import CaptureStatus
from datamimic_ce.authoring.domain.diagnostics import DiagnosticPhase
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1
from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, ReadyBuild, RejectedBuild
from tests_ce.authoring_project import build_document, build_project, entry_digest


@pytest.mark.integration
def test_smoke_reuses_first_capture_and_real_json_exporter(tmp_path: Path, build_executions) -> None:
    result = build_project(tmp_path, build_document(), verification={"smoke_export": True})
    assert isinstance(result, ReadyBuild), result
    assert [request.smoke_export for request in build_executions] == [True, False, False, False]
    smoke = result.verification.smoke_export
    assert smoke.status is VerificationGateStatus.PASSED
    assert (smoke.applicable_exporters, smoke.attempted_exporters, smoke.failed_exporters) == (1, 1, 0)
    assert {path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*")} == {
        "acceptance",
        "acceptance/build.json",
        "datamimic.xml",
    }, "Bounded smoke must not write project artifacts."


@pytest.mark.integration
def test_requested_smoke_without_exporter_is_not_applicable(tmp_path: Path) -> None:
    result = build_project(tmp_path, build_document(exporter=False), verification={"smoke_export": True})
    assert isinstance(result, ReadyBuild), result
    assert result.verification.smoke_export.status is VerificationGateStatus.NOT_APPLICABLE
    assert result.verification.smoke_export.applicable_exporters == 0


@pytest.mark.integration
def test_smoke_export_with_empty_nested_product(tmp_path: Path) -> None:
    result = build_project(
        tmp_path,
        """<setup rngSeed="7">
        <generate name="parents" count="2" target="JSON">
            <key name="id" generator="IncrementGenerator"/>
            <generate name="children" count="0" target="JSON">
                <key name="id" generator="IncrementGenerator"/>
                <key name="parent_id" script="parent.id"/>
            </generate>
        </generate>
        </setup>""",
        verification={"smoke_export": True},
    )
    assert isinstance(result, ReadyBuild), result
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED


@pytest.mark.integration
def test_capped_acceptance_cannot_be_rescued_by_replay(tmp_path: Path, build_executions) -> None:
    # A count range has no declared total, so Build runs it and caps the capture instead of refusing it first.
    document = build_document().model_dump(mode="json")
    properties = document["root"]["children"][0]["properties"]
    del properties["count"]
    properties.update({"min_count": 2, "max_count": 2})
    result = build_project(
        tmp_path,
        DmJsonDocumentV1.model_validate(document),
        max_count=1,
        sample_rows=1,
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "items"}, "count": 2}],
        verification={"deterministic_replay": True},
    )
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.EVIDENCE
    assert len(build_executions) == 1
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED
    # The review binds the declared entry, not a copy rewritten to the cap.
    assert 'maxCount="2"' in (tmp_path / PROJECT_ENTRY_PATH).read_text(encoding="utf-8")
    assert {item.path: item.sha256 for item in result.review_artifact.files}[PROJECT_ENTRY_PATH] == entry_digest(
        tmp_path
    )


@pytest.mark.integration
@pytest.mark.parametrize("traversal_count", ["{1}", "{1/0}"])
def test_dynamic_file_count_never_gets_exhaustion_proof(tmp_path: Path, traversal_count: str) -> None:
    (tmp_path / "rows.csv").write_text("id\n1\n2\n3\n", encoding="utf-8")
    xml = (
        '<setup rngSeed="7"><generate name="rows" source="rows.csv" distribution="ordered" '
        f'count="{traversal_count}" target="JSON"><key name="id" script="this.id"/></generate></setup>'
    )
    result = build_project(
        tmp_path,
        xml,
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 3}],
        verification={"smoke_export": True, "deterministic_replay": True},
    )
    assert isinstance(result, RejectedBuild), result
    assert result.phase is DiagnosticPhase.EVIDENCE
    assert result.evidence[0].capture.status is CaptureStatus.UNKNOWN
    assert result.evidence[0].capture.requested is None
    assert not result.evidence[0].capture.complete
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED
    assert {item.path: item.sha256 for item in result.review_artifact.files}[PROJECT_ENTRY_PATH] == entry_digest(
        tmp_path
    )
