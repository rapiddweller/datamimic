# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A blind agent finds the file-source projection and the place of the written file (#417). The projects are in
tests_ce/scenarios/s13_file_projection; this module checks the texts that lead an agent there."""

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

_PROJECT = Path(__file__).resolve().parents[2] / "scenarios" / "s13_file_projection"


def _copy(tmp_path: Path, variant: str | None = None) -> Path:
    project = tmp_path / "project"
    shutil.copytree(_PROJECT, project)
    if variant is not None:
        shutil.copytree(_PROJECT / "negative" / variant, project, dirs_exist_ok=True)
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
