# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DM211 (SelectorWithoutCountNeedsDbSource): selector= without count=/minCount=/maxCount=
only resolves against a DatabaseClient at runtime (generate_task.py, variable_task.py) - the
error case is covered by test_rule_fixtures.py's fx_selector_without_count.xml. This file
covers the cases DM211 must NOT fire on."""

from pathlib import Path

from datamimic_ce.authoring.linter import lint_descriptor

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_selector_with_count_is_not_flagged() -> None:
    """Happy path: selector= + count= together is always valid, regardless of source type."""
    result = lint_descriptor(_FIXTURES / "fx_selector_with_count.xml")
    rules = {diag.rule for diag in result.diagnostics}
    assert "DM211" not in rules


def test_selector_on_declared_db_source_without_count_is_not_flagged() -> None:
    """Edge case: selector= without count= is valid when source= resolves to a declared
    <database>/<mongodb> client - the one no-count case the runtime actually supports."""
    result = lint_descriptor(_FIXTURES / "fx_selector_db_source_no_count.xml")
    rules = {diag.rule for diag in result.diagnostics}
    assert "DM211" not in rules


def test_nestedkey_selector_without_count_is_not_flagged() -> None:
    """Edge case: <nestedKey> resolves its length from count/minCount/maxCount and falls back
    to the loaded value's length otherwise (nested_key_task.py:_determine_nestedkey_length) -
    it never routes through the DatabaseClient-only check <generate>/<variable> do, so DM211
    deliberately excludes <nestedKey> from its scope."""
    result = lint_descriptor(_FIXTURES / "fx_nestedkey_selector_no_count.xml")
    rules = {diag.rule for diag in result.diagnostics}
    assert "DM211" not in rules
