# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""A script that draws while it loads (W008, #359) is caught by Build's deterministic replay gate; a script that
draws inside a function passes it. The models are the replay models of
functional_tests/test_seeded_load_time_entropy, copied into a project. Build, dry-run and run show W008 as an
authoring warning (#404); tests_ce/scenarios/s14_seeded_library_random has the Build negative. Python, because the
scenario runner checks Build only, not dry-run and run."""

import shutil
from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RunRequest
from datamimic_ce.errors import IssueCode
from tests_ce.authoring_project import build_project

_CORPUS = Path(__file__).resolve().parents[2] / "functional_tests" / "test_seeded_load_time_entropy"
_ROWS = [{"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 3}]
_W008 = ("Seeded Script Draws Entropy While It Loads: script 'leaky.scr.py', line 3.", "W008")


def _build(tmp_path: Path, model: str):
    shutil.copytree(_CORPUS / "script" / "replay", tmp_path / "script" / "replay")
    return build_project(
        tmp_path,
        (_CORPUS / model).read_text(encoding="utf-8"),
        version="5.0",
        expectations=_ROWS,
        verification={"deterministic_replay": True},
    )


def _warnings(diagnostics) -> list[tuple[str, str]]:
    return [
        (item.message, str(item.ce_error.issue_code))
        for item in diagnostics
        if str(item.code) == "engine_warning" and item.ce_error is not None
    ]


def test_build_rejects_a_draw_at_load_time_because_the_replay_differs(tmp_path: Path) -> None:
    result = _build(tmp_path, "replay_leaky.xml")
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status.value == "failed"
    # Next to the failed replay gate. The replay run passes its checks, so Build adds none of its diagnostics.
    assert _warnings(result.diagnostics) == [_W008]


def test_build_accepts_a_draw_inside_a_function(tmp_path: Path) -> None:
    result = _build(tmp_path, "replay_quiet.xml")
    assert result.outcome == "ready", result.diagnostics
    assert result.verification.deterministic_replay.status.value == "passed"
    assert _warnings(result.diagnostics) == []


@pytest.mark.parametrize("phase", ["dry_run", "run"])
def test_dry_run_and_run_show_the_warning_and_stay_ok(tmp_path: Path, phase: str) -> None:
    _build(tmp_path, "replay_leaky.xml")
    application = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH)
    xml = (tmp_path / PROJECT_ENTRY_PATH).read_text(encoding="utf-8")
    request = RunRequest(xml=xml, descriptor_path=PROJECT_ENTRY_PATH)
    result = application.dry_run(request) if phase == "dry_run" else application.run(request)

    assert result.ok, result.diagnostics
    assert _warnings(result.diagnostics) == [_W008]
    warning = next(item for item in result.diagnostics if str(item.code) == "engine_warning")
    assert warning.severity == "warning"
    assert warning.path == ("script", "leaky.scr.py", "line", 3)
    assert warning.ce_error is not None and warning.ce_error.error_code is None
    assert warning.ce_error.issue_code is IssueCode.EXECUTE_SEEDED_LOAD_TIME_ENTROPY
    assert warning.remediation is not None and warning.remediation.startswith("Move the draw into a function")


_ROW = '<generate name="rows" count="1"><key name="id" constant="1"/></generate>'


@pytest.mark.parametrize(
    ("statement", "allow_side_effects", "shown"),
    [
        # W007: bounded execution refuses bash, so only a run with side effects reaches it.
        ('<execute type="bash">echo hi</execute>', True, [("Bash Execution Is Not Deterministic.", "W007")]),
        # W002 renders the <echo> text, which can hold a property value: authoring does not show it.
        ("<echo>value {missing_name}</echo>", False, []),
    ],
)
def test_authoring_shows_only_the_warnings_without_descriptor_values(
    tmp_path: Path, statement: str, allow_side_effects: bool, shown: list[tuple[str, str]]
) -> None:
    xml = f'<setup rngSeed="1">{statement}{_ROW}</setup>'
    (tmp_path / PROJECT_ENTRY_PATH).write_text(xml, encoding="utf-8")
    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).run(
        RunRequest(xml=xml, descriptor_path=PROJECT_ENTRY_PATH, allow_side_effects=allow_side_effects)
    )
    assert result.ok, result.diagnostics
    assert _warnings(result.diagnostics) == shown
