# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A failed <assert> keeps the Build proof of the products made before it (#420). The project and its variants are
tests_ce/scenarios/s21_assert_gate; the scenario runner checks one code per variant. This module checks the facts
that one code cannot carry: what Build kept, what it could not evaluate, and that no property value reaches it."""

import json
import pickle
import shutil
from hashlib import sha256
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters import bounded_executor, dryrun
from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.capture import SmokeExportCapture
from datamimic_ce.authoring.domain.reference import AuthoringLearningReference
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ENTRY_PATH,
    BoundedExecutionRequest,
    ReadyBuild,
    ReferenceRequest,
    ReferenceTopic,
    RejectedBuild,
    RunRequest,
    SourceAccessEvidence,
)
from datamimic_ce.errors import DescriptorLocation, IssueCode, task_config_error
from datamimic_ce.interfaces.cli import app

_PROJECT = Path(__file__).resolve().parents[2] / "scenarios" / "s21_assert_gate"
_NEGATIVES = {item["name"]: item["patch"] for item in json.loads((_PROJECT / "scenario.json").read_text())["negatives"]}


def _copy(tmp_path: Path, negative: str | None) -> Path:
    project = tmp_path / "project"
    shutil.copytree(_PROJECT, project)
    if negative is not None:  # the scenario.json patch is the single source of the variant
        patch = _NEGATIVES[negative]
        target = project / patch["file"]
        target.write_text(target.read_text(encoding="utf-8").replace(patch["old"], patch["new"]), encoding="utf-8")
    return project


def _build(tmp_path: Path, negative: str) -> RejectedBuild:
    result = create_authoring_application(_copy(tmp_path, negative), descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(result, RejectedBuild)
    return result


def _codes(result: RejectedBuild) -> list[str]:
    return [str(item.code) for item in result.diagnostics if item.severity == "error"]


def _not_evaluated(result: RejectedBuild) -> set[str]:
    [item] = [item for item in result.diagnostics if str(item.code) == "not_executed"]
    assert isinstance(item.expected, list)
    return {json.dumps(path) for path in item.expected}


def test_the_failed_row_does_not_change_what_build_keeps(tmp_path: Path) -> None:
    result, *others = (_build(tmp_path / row, f"fails_at_{row}_row") for row in ("first", "middle", "last"))

    for other in others:
        assert [item.model_dump() for item in other.diagnostics] == [item.model_dump() for item in result.diagnostics]
    assert _codes(result) == ["assert_failed", "not_executed"]
    assert [product.name for product in result.evidence] == ["items"]
    assert "Declared product capture is missing." not in result.model_dump_json()
    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.path == ("descriptor", "datamimic.xml", "assert", "line", 11)
    assert failed.message == "The <assert> in 'lines' failed: A line holds at most 4 items"


def test_an_included_step_keeps_every_product_before_it(tmp_path: Path) -> None:
    result = _build(tmp_path, "fails_in_included_step")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.path == ("include", "model/10_stock.xml", "assert", "line", 4)
    assert [product.name for product in result.evidence] == ["items", "lines", "parts"]
    # Only the two checks on the stock product stay unevaluated; the checks on the earlier products passed.
    assert len(_not_evaluated(result)) == 2
    assert _codes(result) == ["assert_failed", "not_executed"]


def test_a_nested_assert_names_its_generate_and_loses_the_whole_outer_product(tmp_path: Path) -> None:
    result = _build(tmp_path, "fails_in_nested_generate")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.path == ("descriptor", "datamimic.xml", "assert", "line", 16)
    assert "in 'parts'" in failed.message
    assert [product.name for product in result.evidence] == ["items"]


def test_an_assert_after_every_product_leaves_nothing_unevaluated(tmp_path: Path) -> None:
    result = _build(tmp_path, "fails_after_all_products")

    assert _codes(result) == ["assert_failed"]
    assert [product.name for product in result.evidence] == ["items", "lines", "parts", "stock"]


def test_an_unrelated_failing_expectation_is_still_reported(tmp_path: Path) -> None:
    result = _build(tmp_path, "assert_and_failing_expectation")

    assert _codes(result) == ["assert_failed", "range", "not_executed"]


@pytest.mark.parametrize("negative", ["message_is_a_property", "message_has_braces", "message_has_dunder"])
def test_a_message_that_can_hold_a_value_is_not_shown(tmp_path: Path, negative: str) -> None:
    result = _build(tmp_path, negative)

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.expected is None
    assert "is not shown" in failed.message
    serialized = result.model_dump_json()
    # A normal run resolves {audit_note} to this value (scenario.json run_error); Build must not show it.
    assert "TOPSECRET-21" not in serialized
    assert "{audit_note}" not in serialized and "__qty__" not in serialized


def test_two_asserts_on_one_line_show_no_message(tmp_path: Path) -> None:
    result = _build(tmp_path, "asserts_share_a_line")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.path == ("descriptor", "datamimic.xml", "assert", "line", 11)
    assert failed.expected is None
    assert "more than one <assert>" in failed.message


def test_authoring_dry_run_is_not_ok_and_shows_the_kept_products(tmp_path: Path) -> None:
    project = _copy(tmp_path, "fails_in_included_step")
    xml = (project / PROJECT_ENTRY_PATH).read_text(encoding="utf-8")

    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).dry_run(
        RunRequest(xml=xml, descriptor_path=PROJECT_ENTRY_PATH, max_count=20)
    )

    assert result.ok is False
    assert [str(item.code) for item in result.diagnostics if item.severity == "error"] == ["assert_failed"]
    assert [product.name for product in result.products] == ["items", "lines", "parts"]


def test_an_assert_without_message_says_so(tmp_path: Path) -> None:
    result = _build(tmp_path, "assert_without_message")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.expected is None
    assert "has no message" in failed.message


def test_a_condition_that_raises_stays_a_broken_expression(tmp_path: Path) -> None:
    result = _build(tmp_path, "condition_raises")

    assert _codes(result) == ["child_execution"]
    assert result.evidence == ()


def test_a_kept_product_that_build_cannot_capture_leaves_every_check_unevaluated(tmp_path: Path) -> None:
    # items completes with an infinite qty; without the failed assert the same value gives child_execution.
    result = _build(tmp_path, "invalid_value_in_a_kept_product")

    assert _codes(result) == ["assert_failed", "child_execution", "not_executed"]
    assert result.evidence == ()
    # The failure envelope, not the dropped capture, carries the read files.
    assert "data/entity/items.json" in _artifact(result)
    [skipped] = [item for item in result.diagnostics if str(item.code) == "not_executed"]
    assert skipped.message == (
        "The run stopped at a failed <assert>. Build kept no capture of these products: items, lines, parts, stock. "
        "Build did not evaluate the 11 checks that read them."
    )


def test_an_assert_in_the_first_product_keeps_a_valid_empty_capture(tmp_path: Path) -> None:
    # No product completed, so the empty stopped capture is valid: no child_execution may claim a lost capture.
    result = _build(tmp_path, "fails_in_first_product")

    assert _codes(result) == ["assert_failed", "not_executed"]
    assert result.evidence == ()
    [skipped] = [item for item in result.diagnostics if str(item.code) == "not_executed"]
    assert skipped.message.startswith(
        "The run stopped at a failed <assert>. Build kept no capture of these products: items, lines, parts, stock."
    )


def test_an_assert_tag_over_several_lines_reports_the_line_where_it_ends(tmp_path: Path) -> None:
    # libxml2 gives an element the line of its start tag's end; the runtime and Build both read that line.
    result = _build(tmp_path, "assert_tag_spans_lines")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert failed.path == ("descriptor", "datamimic.xml", "assert", "line", 13)


def test_a_long_message_is_cut_to_200_characters_in_message_and_expected(tmp_path: Path) -> None:
    result = _build(tmp_path, "message_of_201_characters")

    [failed] = [item for item in result.diagnostics if str(item.code) == "assert_failed"]
    assert isinstance(failed.expected, str) and len(failed.expected) == 200 and failed.expected.endswith("...")
    assert failed.message == f"The <assert> in 'lines' failed: {failed.expected}"


def _project(tmp_path: Path, xml: str, acceptance: object) -> RejectedBuild:
    (tmp_path / "acceptance").mkdir()
    (tmp_path / PROJECT_ENTRY_PATH).write_text(xml, encoding="utf-8")
    (tmp_path / "acceptance" / "build.json").write_text(json.dumps(acceptance), encoding="utf-8")
    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(result, RejectedBuild)
    return result


def test_a_child_product_before_its_failed_parent_keeps_its_count_and_skips_its_foreign_key(tmp_path: Path) -> None:
    result = _project(
        tmp_path,
        """<setup rngSeed="1">
    <generate name="orders" count="3">
        <key name="id" generator="IncrementGenerator"/>
        <key name="cust" script="this.id"/>
    </generate>
    <generate name="customers" count="3">
        <key name="cid" generator="IncrementGenerator"/>
        <assert condition="this.cid &lt; 3" message="customer fails"/>
    </generate>
</setup>""",
        {
            "version": "5.0",
            "product_roles": [
                {"product": "customers", "field": "cid", "role": {"kind": "identifier"}},
                {
                    "product": "orders",
                    "field": "cust",
                    "role": {"kind": "foreign_key", "parent_product": "customers", "parent_field": "cid"},
                },
            ],
            # Wrong on purpose: the kept orders product is evaluated, so its count check reports.
            "expectations": [{"kind": "exact_count", "subject": {"kind": "product", "product": "orders"}, "count": 4}],
        },
    )

    assert _codes(result) == ["assert_failed", "exact_count", "not_executed"]
    assert [product.name for product in result.evidence] == ["orders"]
    assert _not_evaluated(result) == {
        json.dumps(["document", "root", "children", 1]),
        json.dumps(["product_roles", 0]),
        json.dumps(["product_roles", 1]),
    }


def test_one_unevaluated_check_is_named_in_the_singular(tmp_path: Path) -> None:
    result = _project(
        tmp_path,
        """<setup>
    <generate name="a" count="2"><key name="id" generator="IncrementGenerator"/></generate>
    <generate name="b" count="2"><assert condition="False" message="b closes"/></generate>
</setup>""",
        {
            "version": "5.0",
            "expectations": [{"kind": "exact_count", "subject": {"kind": "product", "product": "a"}, "count": 2}],
        },
    )

    [skipped] = [item for item in result.diagnostics if str(item.code) == "not_executed"]
    assert skipped.message.endswith("Build did not evaluate the 1 check that reads them.")


def test_a_forged_stopped_capture_that_does_not_validate_is_refused(tmp_path: Path) -> None:
    error = task_config_error(
        code=IssueCode.TASK_ASSERT_FAILED,
        condition="configured condition",
        extra="",
        location=DescriptorLocation("assert", attribute="condition", line=2),
    )
    forged = dryrun._WorkerSuccess({"a": ({"v": float("inf")},)}, (), (), SmokeExportCapture.not_requested())
    payload = pickle.dumps(dryrun._WorkerFailure(message="m", fix_hint="h", error=error, stopped_capture=forged))

    evidence = bounded_executor._decode_reply(payload, BoundedExecutionRequest(xml="<setup/>"), tmp_path)

    assert [str(item.code) for item in evidence.diagnostics] == ["serialization"]


def _artifact(result: ReadyBuild | RejectedBuild) -> dict[str, str]:
    artifact = result.artifact if isinstance(result, ReadyBuild) else result.review_artifact
    assert artifact is not None
    return {item.path.as_posix(): item.sha256 for item in artifact.files}


def test_the_review_artifact_binds_the_files_the_stopped_run_read(tmp_path: Path) -> None:
    ready = create_authoring_application(_copy(tmp_path / "ready", None), descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(ready, ReadyBuild)
    first = _build(tmp_path / "first", "fails_at_middle_row")
    project = _copy(tmp_path / "second", "fails_at_middle_row")
    items = project / "data" / "entity" / "items.json"
    # A byte that no assert or check reads: the run stops at the same row with the same diagnostics.
    items.write_text(items.read_text(encoding="utf-8").replace('"S1"', '"S9"'), encoding="utf-8")
    second = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(second, RejectedBuild)

    assert [item.model_dump() for item in second.diagnostics] == [item.model_dump() for item in first.diagnostics]
    assert set(_artifact(first)) == set(_artifact(ready))
    assert _artifact(second)["data/entity/items.json"] == sha256(items.read_bytes()).hexdigest()
    assert _artifact(first)["data/entity/items.json"] != _artifact(second)["data/entity/items.json"]


def _stopped_project(tmp_path: Path) -> Path:
    (tmp_path / "data").mkdir()
    for name in ("a", "b", "c", "counted", "late"):
        (tmp_path / "data" / f"{name}.json").write_text('[{"v": 1}]', encoding="utf-8")
    (tmp_path / "model").mkdir()
    (tmp_path / "model" / "step.xml").write_text(
        '<setup><generate name="c" source="data/c.json"/></setup>', encoding="utf-8"
    )
    (tmp_path / "acceptance").mkdir()
    (tmp_path / "acceptance" / "build.json").write_text(
        json.dumps(
            {
                "version": "5.0",
                "expectations": [{"kind": "exact_count", "subject": {"kind": "product", "product": "a"}, "count": 1}],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / PROJECT_ENTRY_PATH).write_text(
        """<setup>
    <include uri="model/step.xml"/>
    <generate name="a" source="data/a.json"/>
    <generate name="b" source="data/b.json"/>
    <generate name="stop" count="1"><assert condition="False" message="stop"/></generate>
    <generate name="late" count="1">
        <variable name="row" source="data/late.json"/>
        <key name="v" script="row.v"/>
    </generate>
    <!-- Build counts the rows of a generate source before the run, so it reads this file before the assert. -->
    <generate name="counted" source="data/counted.json"/>
</setup>""",
        encoding="utf-8",
    )
    return tmp_path


def test_a_stopped_run_lists_the_files_it_read_before_the_assert_and_not_after(tmp_path: Path) -> None:
    project = _stopped_project(tmp_path)
    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    entry = project / PROJECT_ENTRY_PATH
    entry.write_text(
        entry.read_text(encoding="utf-8").replace('condition="False"', 'condition="True"'), encoding="utf-8"
    )
    complete = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, RejectedBuild)
    assert _codes(result) == ["assert_failed", "not_executed"]
    assert sorted(_artifact(result)) == [
        "acceptance/build.json",
        "data/a.json",
        "data/b.json",
        "data/c.json",
        "data/counted.json",
        PROJECT_ENTRY_PATH.as_posix(),
        "model/step.xml",
    ]
    assert set(_artifact(complete)) == {*_artifact(result), "data/late.json"}


def test_a_stopped_run_keeps_its_source_accesses(tmp_path: Path) -> None:
    project = _stopped_project(tmp_path)

    evidence = CeBoundedExecutor(AuthoringWorkspaceContext(project, PROJECT_ENTRY_PATH)).execute(
        BoundedExecutionRequest(
            xml=(project / PROJECT_ENTRY_PATH).read_text(encoding="utf-8"),
            descriptor_path=PROJECT_ENTRY_PATH,
            max_count=20,
        )
    )

    assert evidence.stopped_by_assert
    assert evidence.source_accesses == (SourceAccessEvidence(source_type="file_json", requests=3),)


def test_a_project_that_reads_no_file_binds_only_its_own_files(tmp_path: Path) -> None:
    result = _project(
        tmp_path,
        '<setup><generate name="a" count="1"><assert condition="False" message="a closes"/></generate></setup>',
        {
            "version": "5.0",
            "expectations": [{"kind": "exact_count", "subject": {"kind": "product", "product": "a"}, "count": 1}],
        },
    )

    assert sorted(_artifact(result)) == ["acceptance/build.json", PROJECT_ENTRY_PATH.as_posix()]


@pytest.mark.parametrize(
    ("read_file", "refusal"), [("data/gone.json", "os_error"), ("../outside.json", "serialization")]
)
def test_a_stopped_run_that_names_a_missing_or_outside_file_fails_like_a_success(
    tmp_path: Path, read_file: str, refusal: str
) -> None:
    # The audit hook refuses to remove a snapshot file, so only a forged reply names one; both envelopes refuse it.
    error = task_config_error(
        code=IssueCode.TASK_ASSERT_FAILED,
        condition="configured condition",
        extra="",
        location=DescriptorLocation("assert", attribute="condition", line=2),
    )
    success = dryrun._WorkerSuccess({}, (), (), SmokeExportCapture.not_requested(), read_files=(read_file,))
    stopped = dryrun._WorkerFailure(message="m", fix_hint="h", error=error, read_files=(read_file,))

    def outcome(message: object) -> list[str]:
        try:
            evidence = bounded_executor._decode_reply(
                pickle.dumps(message), BoundedExecutionRequest(xml="<setup/>"), tmp_path
            )
        except OSError:
            return ["os_error"]  # CeBoundedExecutor.execute reports an OSError of the reply as serialization
        return [str(item.code) for item in evidence.diagnostics]

    assert outcome(stopped) == outcome(success) == [refusal]


@pytest.mark.parametrize(("negative", "exit_code"), [(None, 0), ("fails_at_last_row", 1)])
def test_datamimic_run_stops_with_exit_one_only_when_an_assert_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, negative: str | None, exit_code: int
) -> None:
    monkeypatch.chdir(_copy(tmp_path, negative))

    assert CliRunner().invoke(app, ["run", "datamimic.xml"]).exit_code == exit_code


def test_an_assert_in_step_10_still_lists_every_check_it_could_not_evaluate(tmp_path: Path) -> None:
    # S12 r4_above_maximum: only the policy product completes before the assert in positions stops the run.
    s12 = _PROJECT.parent / "s12_personnel_approvals"
    [patch] = [
        item["patch"]
        for item in json.loads((s12 / "scenario.json").read_text())["negatives"]
        if item["name"] == "r4_above_maximum"
    ]
    project = tmp_path / "s12"
    shutil.copytree(s12, project)
    target = project / patch["file"]
    target.write_text(target.read_text(encoding="utf-8").replace(patch["old"], patch["new"]), encoding="utf-8")

    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()

    assert isinstance(result, RejectedBuild)
    assert _codes(result) == ["assert_failed", "not_executed"]
    assert [product.name for product in result.evidence] == ["policy"]
    assert len(_not_evaluated(result)) == 77


def test_the_learning_reference_says_when_to_use_an_assert_or_an_expectation(tmp_path: Path) -> None:
    result = create_authoring_application(tmp_path).reference(
        ReferenceRequest(topic=ReferenceTopic.LEARNING, name="assert_or_expectation")
    )

    [entry] = result.entries or ()
    assert isinstance(entry, AuthoringLearningReference)
    for fact in ("<assert>", "exit code 1", "assert_failed", "not_executed", "exits 0", "literal", "expectations"):
        assert fact in entry.description
    assert (Path(__file__).resolve().parents[3] / entry.path).is_file()
