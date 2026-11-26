# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build names what it did not check (ready_with_gaps) and refuses a project that checks nothing."""

from __future__ import annotations

import hashlib
import json
import re
import shlex
from pathlib import Path, PurePosixPath

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.coverage import CoverageGapKind
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, DiagnosticPhase
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ACCEPTANCE_PATH,
    PROJECT_ENTRY_PATH,
    ReadyBuild,
    ReadyWithGapsBuild,
    ReferenceRequest,
    ReferenceTopic,
    RejectedBuild,
)
from datamimic_ce.interfaces.cli import app
from datamimic_ce.interfaces.cli.presenter import EXIT_READY_WITH_GAPS
from tests_ce.authoring_project import build_project, write_project

_SEEDED = (
    '<setup rngSeed="7"><generate name="cities" count="3">'
    '<key name="id" generator="IncrementGenerator"/></generate></setup>'
)
_UNSEEDED = _SEEDED.replace(' rngSeed="7"', "")
_CITIES = {"kind": "exact_count", "subject": {"kind": "product", "product": "cities"}, "count": 3}
_SHOPS = '<generate name="shops" count="{1 + 1}"><key name="id" generator="IncrementGenerator"/></generate>'


_NO_EXPECTATION = (
    '<setup rngSeed="7"><generate name="rows" count="{1 + 1}"><key name="id" constant="1"/></generate></setup>'
)


def test_an_acceptance_without_expectation_is_refused_after_the_run_with_a_real_example(tmp_path: Path) -> None:
    result = build_project(tmp_path, _NO_EXPECTATION)

    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.EVIDENCE
    (diagnostic,) = result.diagnostics
    assert diagnostic.code == AuthoringRuleId.MISSING_EXPECTATION
    assert diagnostic.phase is DiagnosticPhase.EXPECTATION
    assert diagnostic.path == ("acceptance/build.json", "expectations")
    assert diagnostic.actual == 0
    assert diagnostic.remediation is not None
    assert '"kind": "exact_count"' in diagnostic.remediation
    assert "<" not in diagnostic.remediation


def test_a_run_defect_comes_first_and_missing_expectation_follows(tmp_path: Path) -> None:
    broken = _NO_EXPECTATION.replace('constant="1"', 'script="no_such_name"')

    result = build_project(tmp_path, broken)

    assert isinstance(result, RejectedBuild)
    codes = [item.code for item in result.diagnostics]
    assert codes[-1] == AuthoringRuleId.MISSING_EXPECTATION
    assert len(codes) >= 2
    assert AuthoringRuleId.MISSING_EXPECTATION not in codes[:-1]
    assert next(item for item in result.diagnostics if item.severity == "error").code != (
        AuthoringRuleId.MISSING_EXPECTATION
    )


def _remediation_without_acceptance(tmp_path: Path) -> str:
    (tmp_path / PROJECT_ENTRY_PATH).write_text(_SEEDED, encoding="utf-8")
    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(result, RejectedBuild)
    remediation = result.diagnostics[0].remediation
    assert remediation is not None
    return remediation


def _assembly_guidance() -> str:
    reference = create_authoring_application().reference(ReferenceRequest(topic=ReferenceTopic.ASSEMBLY))
    return str(reference.content)


@pytest.mark.parametrize("source", ["build_remediation", "assembly_guidance"])
def test_every_command_named_in_guidance_exists(tmp_path: Path, source: str) -> None:
    text = _remediation_without_acceptance(tmp_path) if source == "build_remediation" else _assembly_guidance()
    commands = re.findall(r"datamimic [a-z][a-z -]*", text)
    assert commands
    for command in commands:
        args = shlex.split(command.rstrip(" -"))
        assert CliRunner().invoke(app, [*args[1:], "--help"]).exit_code == 0, command


def test_a_project_without_acceptance_file_is_told_to_write_one_expectation(tmp_path: Path) -> None:
    remediation = _remediation_without_acceptance(tmp_path)

    assert '"expectations": [{"kind": "exact_count"' in remediation
    assert '"expectations": []' not in remediation
    assert "datamimic init" in remediation and "datamimic authoring init" in remediation


def test_a_check_derived_from_a_literal_count_avoids_missing_expectation(tmp_path: Path) -> None:
    result = build_project(tmp_path, _SEEDED)

    assert isinstance(result, ReadyBuild), result
    assert result.coverage.expectation_count >= 1


def test_a_seeded_checked_project_is_ready_with_clean_coverage(tmp_path: Path) -> None:
    result = build_project(tmp_path, _SEEDED, expectations=[_CITIES])

    assert isinstance(result, ReadyBuild), result
    assert not result.coverage.has_gaps
    assert result.coverage.seeded
    assert not [item for item in result.diagnostics if item.code == AuthoringRuleId.COVERAGE_GAP]
    assert "action_required" not in result.model_dump(mode="json")
    assert PurePosixPath("acceptance/build.json") == PROJECT_ACCEPTANCE_PATH
    assert PROJECT_ACCEPTANCE_PATH not in result.coverage.unread_data_files


def test_an_unseeded_project_is_ready_with_gaps_and_names_the_seed(tmp_path: Path) -> None:
    result = build_project(tmp_path, _UNSEEDED, expectations=[_CITIES])

    assert isinstance(result, ReadyWithGapsBuild), result
    assert result.outcome == "ready_with_gaps"
    assert result.coverage.open_gaps == (CoverageGapKind.SEEDED,)
    assert result.action_required == (
        "Ready with 1 open coverage gap (seeded). Do not report success until each gap is fixed or explained."
    )
    assert [(item.path, item.severity) for item in result.diagnostics if item.code == AuthoringRuleId.COVERAGE_GAP] == [
        (("coverage", "seeded"), "warning")
    ]
    coverage = result.model_dump(mode="json")["coverage"]
    assert coverage["seeded"] is False
    assert coverage["products_without_expectation"] == []
    assert set(coverage) == {
        "expectation_count",
        "products",
        "products_without_expectation",
        "unread_data_files",
        "unchecked_declared_sinks",
        "seeded",
    }


def test_a_product_without_expectation_is_a_gap_with_counted_facts(tmp_path: Path) -> None:
    entry = _SEEDED.replace("</setup>", f"{_SHOPS}</setup>")

    result = build_project(tmp_path, entry, expectations=[_CITIES])

    assert isinstance(result, ReadyWithGapsBuild), result
    assert {item.product: item.expectations for item in result.coverage.products}["shops"] == 0
    assert result.coverage.products_without_expectation == ("shops",)
    assert result.coverage.open_gaps == (CoverageGapKind.PRODUCTS_WITHOUT_EXPECTATION,)


def _with_data_file(tmp_path: Path, *, read: bool) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "regions.csv").write_text("id|name\n1|north\n2|south\n", encoding="utf-8")
    entry = (
        '<setup rngSeed="7"><generate name="regions" source="data/regions.csv" distribution="ordered"/></setup>'
        if read
        else _SEEDED
    )
    expectation = (
        {"kind": "exact_count", "subject": {"kind": "product", "product": "regions"}, "count": 2} if read else _CITIES
    )
    write_project(tmp_path, entry, expectations=[expectation])


def test_a_data_file_that_no_run_read_is_a_coverage_gap(tmp_path: Path) -> None:
    _with_data_file(tmp_path, read=False)

    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, ReadyWithGapsBuild), result
    assert result.coverage.unread_data_files == (PurePosixPath("data/regions.csv"),)
    assert ("coverage", "unread_data_files") in {item.path for item in result.diagnostics}


def test_a_data_file_that_the_run_read_is_not_a_gap(tmp_path: Path) -> None:
    _with_data_file(tmp_path, read=True)

    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, ReadyBuild), result
    assert result.coverage.unread_data_files == ()


def test_saved_proof_does_not_hide_unread_json_data(tmp_path: Path) -> None:
    result = build_project(tmp_path, _SEEDED, expectations=[_CITIES])
    assert isinstance(result, ReadyBuild), result
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "model-proof.json").write_text(result.model_dump_json(), encoding="utf-8")

    application = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH)
    with_proof = application.build()
    assert isinstance(with_proof, ReadyBuild), with_proof

    run = CliRunner().invoke(app, ["authoring", "run-project", str(tmp_path)])
    assert run.exit_code == 0, run.stdout
    assert json.loads(run.stdout)["build_outcome"] == "ready"

    (tmp_path / "unread.json").write_text("[]", encoding="utf-8")
    with_unread = application.build()
    assert isinstance(with_unread, ReadyWithGapsBuild), with_unread
    assert with_unread.coverage.unread_data_files == (PurePosixPath("unread.json"),)


_PREVIOUS_EXPORT = PurePosixPath("output/previous/regions.csv")


def _with_previous_export(tmp_path: Path, *, read: bool) -> bytes:
    content = b"id|name\n1|north\n2|south\n"
    (tmp_path / _PREVIOUS_EXPORT).parent.mkdir(parents=True)
    (tmp_path / _PREVIOUS_EXPORT).write_bytes(content)
    entry = (
        f'<setup rngSeed="7"><generate name="regions" source="{_PREVIOUS_EXPORT}" distribution="ordered"/></setup>'
        if read
        else _SEEDED
    )
    expectation = (
        {"kind": "exact_count", "subject": {"kind": "product", "product": "regions"}, "count": 2} if read else _CITIES
    )
    write_project(tmp_path, entry, expectations=[expectation])
    return content


def test_a_model_that_reads_a_previous_export_under_output_is_proven_on_its_bytes(tmp_path: Path) -> None:
    content = _with_previous_export(tmp_path, read=True)

    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, ReadyBuild), result
    assert result.coverage.unread_data_files == ()
    digests = {item.path: item.sha256 for item in result.artifact.files}
    assert digests[_PREVIOUS_EXPORT] == hashlib.sha256(content).hexdigest()
    regions = next(item for item in result.evidence if item.name == "regions")
    assert [row["name"] for row in regions.rows] == ["north", "south"]


def test_a_previous_export_that_the_model_does_not_read_is_neither_a_gap_nor_proof_input(tmp_path: Path) -> None:
    _with_previous_export(tmp_path, read=False)

    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, ReadyBuild), result
    assert result.coverage.unread_data_files == ()
    assert _PREVIOUS_EXPORT not in {item.path for item in result.artifact.files}


def test_documentation_and_library_files_are_not_unread_data(tmp_path: Path) -> None:
    for folder in ("docs", "lib"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "table.csv").write_text("id\n1\n", encoding="utf-8")
    (tmp_path / "README.txt").write_text("notes", encoding="utf-8")

    result = build_project(tmp_path, _SEEDED, expectations=[_CITIES])

    assert isinstance(result, ReadyBuild), result


def test_the_documented_exempt_folders_are_the_ones_that_the_code_exempts() -> None:
    """#691: the reference names every exempt root, folder and name prefix; one list in code, one in the text."""
    from datamimic_ce.authoring.domain.coverage import NON_DATA_FOLDERS, NON_DATA_NAME_PREFIXES, NON_DATA_ROOTS

    root = Path(__file__).resolve().parents[3] / "plugins/datamimic/skills/generate-test-data/references"
    text = (root / "ce.md").read_text(encoding="utf-8")
    for name in (*NON_DATA_ROOTS, *NON_DATA_FOLDERS, *NON_DATA_NAME_PREFIXES):
        assert f"`{name}" in text, name


def test_the_ready_json_lists_each_expectation_declared_and_derived(tmp_path: Path) -> None:
    result = build_project(tmp_path, _SEEDED, expectations=[{**_CITIES, "count": 3}])

    assert isinstance(result, ReadyBuild), result
    payload = result.model_dump(mode="json")
    items = payload["expectations"]["items"]
    assert len(items) == payload["expectations"]["total"] == payload["coverage"]["expectation_count"]
    assert {item["origin"] for item in items} == {"model", "derived"}
    assert {item["result"] for item in items} == {"passed"}


def test_the_workspace_lists_only_regular_files_sorted_and_relative(tmp_path: Path) -> None:
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext

    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "two.csv").write_text("x", encoding="utf-8")
    (tmp_path / "a.csv").write_text("x", encoding="utf-8")
    (tmp_path / "link.csv").symlink_to(tmp_path / "a.csv")
    (tmp_path / "linked_dir").symlink_to(tmp_path / "b", target_is_directory=True)

    listed = AuthoringWorkspaceContext(tmp_path).list_project_files()

    assert listed == (PurePosixPath("a.csv"), PurePosixPath("b/two.csv"))


def _cli_build(tmp_path: Path, *extra: str):
    return CliRunner().invoke(app, ["authoring", "build", str(tmp_path), *extra])


def test_the_cli_exits_0_for_ready_and_3_for_ready_with_gaps_and_1_for_rejected(tmp_path: Path) -> None:
    ready, gaps, rejected = (tmp_path / name for name in ("ready", "gaps", "rejected"))
    for root in (ready, gaps, rejected):
        root.mkdir()
    write_project(ready, _SEEDED, expectations=[_CITIES])
    write_project(gaps, _UNSEEDED, expectations=[_CITIES])
    write_project(rejected, _SEEDED.replace('count="3"', 'count="{1 + 2}"'))

    results = {name: _cli_build(root) for name, root in (("ready", ready), ("gaps", gaps), ("rejected", rejected))}

    assert {name: result.exit_code for name, result in results.items()} == {
        "ready": 0,
        "gaps": EXIT_READY_WITH_GAPS,
        "rejected": 1,
    }
    assert EXIT_READY_WITH_GAPS == 3
    assert {name: json.loads(result.stdout)["outcome"] for name, result in results.items()} == {
        "ready": "ready",
        "gaps": "ready_with_gaps",
        "rejected": "rejected",
    }


def test_the_text_format_names_the_gaps_and_the_action(tmp_path: Path) -> None:
    write_project(tmp_path, _UNSEEDED, expectations=[_CITIES])

    result = _cli_build(tmp_path, "--format", "text")

    assert result.exit_code == EXIT_READY_WITH_GAPS
    assert "Status: Ready with gaps" in result.stdout
    assert "Action required: Ready with 1 open coverage gap (seeded)." in result.stdout


def test_the_build_help_documents_the_exit_codes() -> None:
    result = CliRunner().invoke(app, ["authoring", "build", "--help"])

    assert "ready_with_gaps" in result.stdout
    assert "Exit code 3: ready_with_gaps" in result.stdout


def test_the_published_build_result_schema_has_all_three_outcomes() -> None:
    result = CliRunner().invoke(app, ["authoring", "schema", "--name", "build_result"])

    schema = json.loads(result.stdout)
    assert set(schema["discriminator"]["mapping"]) == {"ready", "ready_with_gaps", "rejected"}
    gaps = schema["$defs"]["ReadyWithGapsBuild"]
    assert {"action_required", "coverage", "artifact", "evidence"} <= set(gaps["required"])
