# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build tells an agent why a script failed and how to join a second file (campaign b3, e07).

Python-only: the scenario harness checks the diagnostic code and issue, not the remediation text. Each case
patches tests_ce/scenarios/s31_file_lookup, so the descriptor stays the checked-in DSL project."""

import shutil
from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RejectedBuild
from datamimic_ce.authoring.domain.rule_catalog import authoring_rule_definition
from datamimic_ce.authoring.domain.script_semantics import LibraryRefusal, LibraryRefusalReason
from datamimic_ce.engine.runtime.scripting.expression_globals import SCRIPT_BUILTINS, UNOFFERED_BUILTINS
from datamimic_ce.errors import (
    GUIDANCE_FILE_LOOKUP,
    GUIDANCE_LOOKUP_POINTER,
    GUIDANCE_SCRIPT_BUILTIN,
    GUIDANCE_WHERE_SCOPE,
)

_SCENARIO = Path(__file__).parents[2] / "scenarios" / "s31_file_lookup"
_LOOKUP = '<variable name="branch" script="{b.branch_id: b for b in branches}.get(branch_id)"/>'


def _remediations(tmp_path: Path, old: str, new: str) -> dict[str, str]:
    project = tmp_path / "project"
    shutil.copytree(_SCENARIO, project)
    descriptor = project / "datamimic.xml"
    text = descriptor.read_text(encoding="utf-8")
    assert text.count(old) == 1
    descriptor.write_text(text.replace(old, new), encoding="utf-8")
    built = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()
    assert isinstance(built, RejectedBuild)
    return {str(item.code): str(item.remediation) for item in built.diagnostics}


@pytest.mark.parametrize(
    "script",
    [
        "next((b for b in branches if b.branch_id == branch_id), None)",
        "open('data/entity/branches.ent.csv').read()",
    ],
    ids=["next", "open"],
)
def test_build_gives_the_builtin_replacements_and_the_lookup(tmp_path: Path, script: str) -> None:
    remediation = _remediations(tmp_path, _LOOKUP, f'<variable name="branch" script="{script}"/>')["child_execution"]

    assert remediation == GUIDANCE_SCRIPT_BUILTIN


def test_the_builtin_guidance_names_only_what_scripts_lack_and_offer() -> None:
    assert {"next", "isinstance", "open"} <= UNOFFERED_BUILTINS
    assert "type" in SCRIPT_BUILTINS and "type(x) is str" in GUIDANCE_SCRIPT_BUILTIN


def test_build_says_where_reads_one_row_and_gives_the_lookup(tmp_path: Path) -> None:
    remediation = _remediations(
        tmp_path,
        'columns="account_id, branch_id">',
        'columns="account_id, branch_id" where="branch_id != parent.closed_branch">',
    )["child_execution"]

    assert remediation == GUIDANCE_WHERE_SCOPE and GUIDANCE_FILE_LOOKUP in remediation


def test_build_keeps_the_scope_hint_for_a_key_script(tmp_path: Path) -> None:
    remediation = _remediations(tmp_path, "script=\"branch.city if branch else 'UNKNOWN'\"", 'script="parent.city"')[
        "child_execution"
    ]

    assert remediation != GUIDANCE_WHERE_SCOPE and "parent.name" in remediation


@pytest.mark.parametrize("element", ["variable", "nestedKey"])
def test_where_on_a_value_element_points_to_the_lookup(tmp_path: Path, element: str) -> None:
    remediation = _remediations(
        tmp_path, _LOOKUP, f'<{element} name="branch" source="data/entity/branches.ent.csv" where="branch_id == x"/>'
    )["DM103"]

    assert remediation.endswith(f"where= keeps rows of a <generate> or <iterate> file source. {GUIDANCE_FILE_LOOKUP}")


def test_the_refusals_of_other_join_attempts_point_to_the_lookup() -> None:
    """Python-only: static catalog text. Agents reached DM211 (a selector), DM407 (a nested generate) and the
    <execute> file-builtin refusal while they tried to join a second file (campaign b3, e07)."""
    for rule_id in ("DM211", "DM407"):
        assert authoring_rule_definition(rule_id).fix_hint.endswith(GUIDANCE_LOOKUP_POINTER), rule_id
    refusal = LibraryRefusal(LibraryRefusalReason.FILE_OR_DYNAMIC_CODE_BUILTIN, line=1)
    assert refusal.remediation().endswith(GUIDANCE_LOOKUP_POINTER)
