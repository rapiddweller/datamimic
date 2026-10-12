from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from script.architecture_study import service_evidence_ledger as ledger_module
from script.architecture_study.service_inventory import REPO, build_report

_HISTORICAL_EVIDENCE = {
    "tests_ce/integration_tests/test_composite_reference/composite_exhausted.xml": (
        "normalized_error",
        "docs/architecture/refactoring-study/experiment-2/step-08c22.md",
    ),
    "tests_ce/integration_tests/test_execute_script/execute_script_and_body.xml": (
        "normalized_error",
        "docs/architecture/refactoring-study/experiment-2/step-08c22.md",
    ),
    "tests_ce/integration_tests/test_execute_script/execute_script_and_uri.xml": (
        "normalized_error",
        "docs/architecture/refactoring-study/experiment-2/step-08c22.md",
    ),
    "tests_ce/integration_tests/test_execute_script/execute_script_non_string.xml": (
        "normalized_error",
        "docs/architecture/refactoring-study/experiment-2/step-08c22.md",
    ),
    "tests_ce/integration_tests/test_iterate_offset/test_offset_client_rejected.xml": (
        "normalized_error",
        "docs/architecture/refactoring-study/experiment-2/step-08c22.md",
    ),
    "tests_ce/integration_tests/test_page_process/test_page_process_sqlite.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c24.md",
    ),
    "tests_ce/integration_tests/test_reference_distribution/ref_ordered_exhausted.xml": (
        "normalized_error",
        "docs/architecture/refactoring-study/experiment-2/step-08c22.md",
    ),
    "tests_ce/integration_tests/test_reference_distribution/ref_unique_cyclic_invalid.xml": (
        "normalized_error",
        "docs/architecture/refactoring-study/experiment-2/step-08c22.md",
    ),
    "tests_ce/integration_tests/test_source_read_determinism/sqlite_seeded.xml": (
        "exact_seeded",
        "docs/architecture/refactoring-study/experiment-2/verification-2026-09-23.md",
    ),
    "tests_ce/integration_tests/test_sql_crud_targets/sql_update_no_pk.xml": (
        "normalized_error",
        "docs/architecture/refactoring-study/experiment-2/step-08c22.md",
    ),
    "tests_ce/external_service_tests/test_rdbms/test_postgresql_local.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c27.md",
    ),
    "tests_ce/external_service_tests/test_mongodb/test_mongodb_pagination_happy.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c28.md",
    ),
    "tests_ce/external_service_tests/test_mongodb/test_mongodb_pagination_edge.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c30.md",
    ),
    "tests_ce/external_service_tests/test_mongodb/test_mongodb_decimal.xml": (
        "exact_seeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c30.md",
    ),
    "tests_ce/external_service_tests/data_source_cyclic/test_csv_cyclic_mp.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/data_source_cyclic/test_csv_cyclic_non_mp.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/data_source_cyclic/test_json_cyclic.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/data_source_cyclic/test_json_cyclic_non_mp.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/data_source_cyclic/test_memstore_product_cyclic.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/data_source_cyclic/test_part_cyclic_mp.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/data_source_cyclic/test_part_memstore_cyclic.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/data_source_cyclic/test_part_no_cyclic.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/integration_data_source_cyclic/test_csv_cyclic.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/integration_data_source_cyclic/test_json_cyclic.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
    "tests_ce/external_service_tests/integration_data_source_cyclic/test_product_cyclic.xml": (
        "normalized_unseeded",
        "docs/architecture/refactoring-study/experiment-2/step-08c33.md",
    ),
}

_STATUS_SEMANTICS = (
    "Statuses describe comparisons recorded in evidence_ref; UNVERIFIED means no admitted "
    "historical per-path evidence, and no status certifies current-HEAD parity."
)


def _evidence_tuple(entry: dict[str, str]) -> tuple[str, str, str]:
    return entry["path"], entry["status"], entry["evidence_ref"]


def test_cli_preserves_live_scope_and_all_historical_evidence() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "script.architecture_study.service_evidence_ledger"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    live_paths = {entry["path"] for entry in build_report()["entries"]}
    entries = report["entries"]
    supplemental = report["historical_out_of_scope_entries"]

    assert report["current_parity_status"] == "not-assessed"
    assert report["evidence_scope"] == "historical-revision-bound"
    assert report["status_semantics"] == _STATUS_SEMANTICS
    assert [entry["path"] for entry in entries] == sorted(live_paths)
    assert [entry["path"] for entry in supplemental] == sorted(entry["path"] for entry in supplemental)
    assert report["service_path_count"] == len(live_paths) == len(entries)
    assert report["counts"] == dict(sorted(Counter(entry["status"] for entry in entries).items()))
    assert sum(report["counts"].values()) == len(entries)

    evidence_entries = [entry for entry in entries if entry["evidence_ref"] is not None]
    actual = Counter(_evidence_tuple(entry) for entry in [*evidence_entries, *supplemental])
    expected = Counter(
        (path, evidence_class, reference) for path, (evidence_class, reference) in _HISTORICAL_EVIDENCE.items()
    )
    assert len(expected) == 25
    assert actual == expected
    assert all(actual[record] == 1 for record in expected)


@pytest.mark.parametrize(
    ("inventory_paths", "evidence_rows", "message"),
    [
        (["a.xml", "a.xml"], {}, "duplicate paths"),
        (
            ["a.xml"],
            {
                "b.xml": (
                    "exact_seeded",
                    "docs/architecture/refactoring-study/experiment-2/step-08c22.md",
                )
            },
            "not in service inventory",
        ),
    ],
)
def test_strict_builder_rejects_duplicate_or_out_of_scope_paths(
    inventory_paths: list[str], evidence_rows: dict[str, tuple[str, str]], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        ledger_module.build_ledger(inventory_paths, evidence_rows)


@pytest.fixture
def temporary_evidence_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    monkeypatch.setattr(ledger_module, "REPO", tmp_path)
    descriptor = "tests_ce/local/case.xml"
    descriptor_file = tmp_path / descriptor
    descriptor_file.parent.mkdir(parents=True)
    descriptor_file.write_text("<setup />", encoding="utf-8")
    reference = "docs/architecture/refactoring-study/experiment-2/evidence.md"
    reference_file = tmp_path / reference
    reference_file.parent.mkdir(parents=True)
    reference_file.write_text("historical record\n", encoding="utf-8")
    return descriptor, reference


def test_supplemental_evidence_rejects_invalid_class(
    temporary_evidence_workspace: tuple[str, str],
) -> None:
    descriptor, reference = temporary_evidence_workspace

    with pytest.raises(ValueError, match="invalid evidence class"):
        ledger_module.validate_and_partition_evidence([], {descriptor: ("current_parity", reference)}, {descriptor})


def test_supplemental_evidence_rejects_missing_reference(
    temporary_evidence_workspace: tuple[str, str],
) -> None:
    descriptor, _ = temporary_evidence_workspace

    with pytest.raises(ValueError, match="invalid experiment-2 evidence reference"):
        ledger_module.validate_and_partition_evidence(
            [],
            {descriptor: ("exact_seeded", "docs/architecture/refactoring-study/experiment-2/missing.md")},
            {descriptor},
        )


@pytest.mark.parametrize(
    "row",
    [
        ["exact_seeded", "docs/architecture/refactoring-study/experiment-2/evidence.md"],
        ("exact_seeded",),
        ("exact_seeded", "docs/architecture/refactoring-study/experiment-2/evidence.md", "extra"),
    ],
)
def test_supplemental_evidence_rejects_malformed_pair(
    temporary_evidence_workspace: tuple[str, str], row: object
) -> None:
    descriptor, _ = temporary_evidence_workspace

    with pytest.raises(ValueError, match="invalid evidence tuple"):
        ledger_module.validate_and_partition_evidence([], {descriptor: row}, {descriptor})


def test_supplemental_evidence_rejects_unsafe_descriptor_path(
    temporary_evidence_workspace: tuple[str, str],
) -> None:
    _, reference = temporary_evidence_workspace

    with pytest.raises(ValueError, match="invalid descriptor path"):
        ledger_module.validate_and_partition_evidence(
            [], {"../outside.xml": ("exact_seeded", reference)}, {"../outside.xml"}
        )


def test_supplemental_evidence_rejects_untracked_descriptor(
    temporary_evidence_workspace: tuple[str, str],
) -> None:
    descriptor, reference = temporary_evidence_workspace

    with pytest.raises(ValueError, match="evidence descriptor is not tracked"):
        ledger_module.validate_and_partition_evidence([], {descriptor: ("exact_seeded", reference)}, set())


def test_supplemental_evidence_rejects_tracked_but_deleted_descriptor(
    temporary_evidence_workspace: tuple[str, str], tmp_path: Path
) -> None:
    descriptor, reference = temporary_evidence_workspace
    (tmp_path / descriptor).unlink()

    with pytest.raises(ValueError, match="evidence descriptor is missing"):
        ledger_module.validate_and_partition_evidence([], {descriptor: ("exact_seeded", reference)}, {descriptor})


def test_main_emits_no_success_json_for_invalid_supplemental_evidence(
    temporary_evidence_workspace: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    descriptor, reference = temporary_evidence_workspace
    monkeypatch.setattr(ledger_module, "build_report", lambda: {"entries": []})
    monkeypatch.setattr(ledger_module, "tracked_descriptor_paths", lambda: {descriptor})
    monkeypatch.setattr(ledger_module, "EVIDENCE", {descriptor: ("invalid", reference)})
    monkeypatch.setattr(sys, "argv", ["service_evidence_ledger"])

    with pytest.raises(ValueError, match="invalid evidence class"):
        ledger_module.main()

    assert capsys.readouterr().out == ""


def test_supplemental_evidence_rejects_symlink_outside_repository(
    temporary_evidence_workspace: tuple[str, str],
    tmp_path: Path,
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    _, reference = temporary_evidence_workspace
    descriptor = "tests_ce/local/escape.xml"
    outside_file = tmp_path_factory.mktemp("outside-repository") / "case.xml"
    outside_file.write_text("<setup />", encoding="utf-8")
    symlink = tmp_path / descriptor
    try:
        symlink.symlink_to(outside_file)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"symlinks are unavailable: {error}")

    with pytest.raises(ValueError, match="missing or outside the repository"):
        ledger_module.validate_and_partition_evidence([], {descriptor: ("exact_seeded", reference)}, {descriptor})


def test_git_tracking_failure_emits_no_success_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(ledger_module, "REPO", tmp_path)
    monkeypatch.setattr(ledger_module, "build_report", lambda: {"entries": []})
    monkeypatch.setattr(sys, "argv", ["service_evidence_ledger"])

    def fail_git(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(128, ["git", "ls-files"], stderr="index unavailable")

    monkeypatch.setattr(ledger_module.subprocess, "run", fail_git)

    with pytest.raises(subprocess.CalledProcessError) as error:
        ledger_module.main()

    assert error.value.stderr == "index unavailable"
    assert capsys.readouterr().out == ""
