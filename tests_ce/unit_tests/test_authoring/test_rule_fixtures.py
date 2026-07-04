# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Fixture-driven lint regression: every fixture descriptor seeds known violations;
the linter must report (at least) exactly those rule ids. Doubles as the eval set."""

from pathlib import Path

import pytest

from datamimic_ce.authoring import lint_descriptor

_FIXTURES = Path(__file__).resolve().parent / "fixtures"

# fixture -> rule ids that MUST be reported (subset match: broad hints like DM303 may add to it)
EXPECTED: dict[str, set[str]] = {
    "fx_xml_syntax.xml": {"DM001"},
    "fx_unknown_element.xml": {"DM101"},
    "fx_bad_nesting.xml": {"DM102", "DM107"},
    "fx_typo_attribute.xml": {"DM103"},
    "fx_missing_required.xml": {"DM104"},
    "fx_bad_enum.xml": {"DM105"},
    "fx_root_not_setup.xml": {"DM106"},
    "fx_dead_attr.xml": {"DM103"},  # bucket was purged EE surface -> unknown attribute
    "fx_count_conflicts.xml": {"DM201", "DM212"},
    "fx_missing_count.xml": {"DM202"},
    "fx_key_two_modes.xml": {"DM203"},
    "fx_unique_misuse.xml": {"DM204"},
    "fx_source_modes.xml": {"DM205", "DM214"},
    "fx_nestedkey_cyclic.xml": {"DM213"},
    "fx_memory_and_seed.xml": {"DM301", "DM302", "DM303"},
    "fx_seed_multiprocess_pagesize.xml": {"DM304", "DM305"},
    "fx_upsert_zero.xml": {"DM307"},
    "fx_generator_strings.xml": {"DM310", "DM311"},
    "fx_undeclared_refs.xml": {"DM401", "DM403"},
    "fx_engine_fallback.xml": {"DM000"},
    "fx_script_interpolation.xml": {"DM314"},
    "fx_nestedkey_no_type.xml": {"DM216"},
}


@pytest.mark.parametrize("fixture", sorted(EXPECTED))
def test_fixture_reports_seeded_rules(fixture: str) -> None:
    result = lint_descriptor(_FIXTURES / fixture)
    found = {diag.rule for diag in result.diagnostics}
    missing = EXPECTED[fixture] - found
    assert not missing, f"{fixture}: expected {missing} in {sorted(found)}"


def test_every_fixture_produces_diagnostics() -> None:
    for fixture in EXPECTED:
        result = lint_descriptor(_FIXTURES / fixture)
        assert result.diagnostics, f"{fixture} should produce at least one diagnostic"


def test_clean_descriptor_is_ok() -> None:
    result = lint_descriptor(_FIXTURES / "fx_clean.xml")
    errors = [d for d in result.diagnostics if d.severity.value == "error"]
    assert result.ok and not errors, [d.message for d in result.diagnostics]


def test_typo_fix_hint_carries_did_you_mean() -> None:
    result = lint_descriptor(_FIXTURES / "fx_typo_attribute.xml")
    typo = next(d for d in result.diagnostics if d.rule == "DM103")
    assert "pageSize" in typo.fix_hint


def test_diagnostics_carry_location_and_hint() -> None:
    result = lint_descriptor(_FIXTURES / "fx_typo_attribute.xml")
    for diag in result.diagnostics:
        assert diag.fix_hint, f"{diag.rule} without fix_hint"
        assert diag.path.startswith("/"), diag
        assert diag.line is None or diag.line >= 1
