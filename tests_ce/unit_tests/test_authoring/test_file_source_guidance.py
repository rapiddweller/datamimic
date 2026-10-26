# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A blind agent finds the file-source projection and the place of the written file (#417). The projects are in
tests_ce/scenarios/s13_file_projection; this module checks the texts that lead an agent there."""

import json
import shutil
from pathlib import Path

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.reference import AuthoringLearningReference
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ACCEPTANCE_PATH,
    PROJECT_ENTRY_PATH,
    ReadyBuild,
    ReferenceRequest,
    ReferenceTopic,
    RejectedBuild,
)
from tests_ce.authoring_project import build_project

_PROJECT = Path(__file__).resolve().parents[2] / "scenarios" / "s13_file_projection"


def _copy(tmp_path: Path, negative: str | None = None) -> Path:
    project = tmp_path / "project"
    shutil.copytree(_PROJECT, project)
    if negative is not None:  # the scenario.json patch is the single source of the variant
        negatives = json.loads((_PROJECT / "scenario.json").read_text(encoding="utf-8"))["negatives"]
        [patch] = [item["patch"] for item in negatives if item["name"] == negative]
        target = project / patch["file"]
        target.write_text(target.read_text(encoding="utf-8").replace(patch["old"], patch["new"]), encoding="utf-8")
    return project


def test_learning_reference_names_the_projection_and_the_output_place(tmp_path: Path) -> None:
    result = create_authoring_application(tmp_path).reference(
        ReferenceRequest(topic=ReferenceTopic.LEARNING, name="file_sources")
    )

    [entry] = result.entries or ()
    assert isinstance(entry, AuthoringLearningReference)
    for fact in ("<variable", "field_absent", "datamimic run datamimic.xml", "output/", "exportUri"):
        assert fact in entry.description
    assert (Path(__file__).resolve().parents[3] / entry.path).is_file()


def test_field_absent_on_a_source_column_points_to_the_projection(tmp_path: Path) -> None:
    project = _copy(tmp_path, "generate_source_copies_columns")

    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, RejectedBuild)
    [absent] = [item for item in result.diagnostics if str(item.code) == "field_absent"]
    assert "<variable" in str(absent.remediation)
    assert "--name file_sources" in str(absent.remediation)


def test_a_passed_smoke_export_says_that_only_datamimic_run_writes_the_file(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    acceptance = project / PROJECT_ACCEPTANCE_PATH
    acceptance.write_text(
        acceptance.read_text(encoding="utf-8").replace(
            '"version": "5.0",', '"version": "5.0", "verification": {"smoke_export": true},'
        ),
        encoding="utf-8",
    )

    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, ReadyBuild), result.diagnostics
    assert "datamimic run datamimic.xml" in result.verification.smoke_export.reason
    assert not (project / "output").exists()


def test_a_default_build_with_a_target_says_where_datamimic_run_writes(tmp_path: Path) -> None:
    """The blind e04 run built without smoke export first; that Build must already name the output place."""
    project = _copy(tmp_path, "generate_source_copies_columns")
    acceptance = project / PROJECT_ACCEPTANCE_PATH
    acceptance.write_text('{"version": "5.0"}', encoding="utf-8")

    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, ReadyBuild), result.diagnostics
    assert "datamimic run datamimic.xml" in result.verification.smoke_export.reason
    assert "output/" in result.verification.smoke_export.reason


def test_a_default_build_without_a_target_keeps_the_plain_reason(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    entry = project / PROJECT_ENTRY_PATH
    entry.write_text(
        entry.read_text(encoding="utf-8").replace(' target="JSON" exportUri="priced_orders"', ""), encoding="utf-8"
    )

    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, ReadyBuild), result.diagnostics
    assert result.verification.smoke_export.reason == "Smoke export was not requested"


def test_a_default_build_with_only_a_memstore_target_keeps_the_plain_reason(tmp_path: Path) -> None:
    """A memstore is read back in the same run; datamimic run writes nothing for it under output/."""
    xml = (
        '<setup rngSeed="7"><memstore id="mem"/><generate name="parents" count="3" target="mem">'
        '<key name="id" generator="IncrementGenerator"/></generate><generate name="readback" source="mem" '
        'type="parents" distribution="ordered"><key name="id" script="this.id"/></generate></setup>'
    )
    roles = (
        {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
        {
            "product": "readback",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
        },
    )

    result = build_project(tmp_path, xml, product_roles=roles)

    assert isinstance(result, ReadyBuild), result.diagnostics
    assert result.verification.smoke_export.reason == "Smoke export was not requested"
