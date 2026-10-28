# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build tells an agent why a script failed and how to join a second file (campaign b3, e07).

The Build remediations of the s31 negatives are checked in s31/scenario.json. What stays here has no one-text
patch of s31 (a <nestedKey> with where=) or is static catalog text."""

import builtins
import shutil
from pathlib import Path

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, RejectedBuild
from datamimic_ce.authoring.domain.rule_catalog import authoring_rule_definition
from datamimic_ce.authoring.domain.script_semantics import LibraryRefusal, LibraryRefusalReason
from datamimic_ce.engine.runtime.scripting.expression_globals import SAFE_GLOBALS, UNOFFERED_BUILTINS
from datamimic_ce.errors import (
    GUIDANCE_FILE_LOOKUP,
    GUIDANCE_LOOKUP_POINTER,
    GUIDANCE_SCRIPT_BUILTIN,
    SCRIPT_BUILTIN_NAMES,
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


def test_the_builtin_guidance_lists_exactly_the_builtins_in_the_script_globals() -> None:
    """Python-only: the errors layer cannot import the engine globals, so this pins the two equal."""
    assert tuple(sorted(SAFE_GLOBALS.keys() & set(dir(builtins)))) == SCRIPT_BUILTIN_NAMES
    assert {"next", "isinstance", "open"} <= UNOFFERED_BUILTINS
    assert "type" in SCRIPT_BUILTIN_NAMES and "type(x) is str" in GUIDANCE_SCRIPT_BUILTIN


def test_where_on_a_nested_key_points_to_the_lookup(tmp_path: Path) -> None:
    """The <variable> case is the s31 negative a_variable_has_no_where; s31 has no <nestedKey> to patch in one text."""
    remediation = _remediations(
        tmp_path, _LOOKUP, '<nestedKey name="branch" source="data/entity/branches.ent.csv" where="branch_id == x"/>'
    )["DM103"]

    assert remediation.endswith(f"where= keeps rows of a <generate> or <iterate> file source. {GUIDANCE_FILE_LOOKUP}")


def test_the_refusals_of_other_join_attempts_point_to_the_lookup() -> None:
    """Python-only: static catalog text. Agents reached DM211 (a selector), DM407 (a nested generate) and the
    <execute> file-builtin refusal while they tried to join a second file (campaign b3, e07)."""
    for rule_id in ("DM211", "DM407"):
        assert authoring_rule_definition(rule_id).fix_hint.endswith(GUIDANCE_LOOKUP_POINTER), rule_id
    refusal = LibraryRefusal(LibraryRefusalReason.FILE_OR_DYNAMIC_CODE_BUILTIN, line=1)
    assert refusal.remediation().endswith(GUIDANCE_LOOKUP_POINTER)
