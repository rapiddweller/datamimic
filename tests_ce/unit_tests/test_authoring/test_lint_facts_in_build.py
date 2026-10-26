# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build keeps the attribute names of a lint finding (#426): blind agents wrote minimum= on a key, and min=/max=
on a key with generator=. The descriptors are the ones from those runs."""

from pathlib import Path

import pytest

from datamimic_ce.authoring.domain.requests import RejectedBuild
from tests_ce.authoring_project import build_project


def _rejected(tmp_path: Path, key: str) -> RejectedBuild:
    xml = f'<setup rngSeed="1"><generate name="offers" count="2">{key}</generate></setup>'
    result = build_project(tmp_path, xml)
    assert isinstance(result, RejectedBuild)
    return result


@pytest.mark.parametrize(
    ("key", "code", "hint"),
    [
        pytest.param(
            '<key name="price" type="int" minimum="50" max="900"/>',
            "DM103",
            "Attribute 'minimum' is unknown on <key>. Did you mean 'min'?",
            id="unknown-attribute",
        ),
        pytest.param(
            '<key name="price" generator="IntegerGenerator" min="100" max="900"/>',
            "DM214",
            "Required: type=.",
            id="companion-without-mode",
        ),
        pytest.param(
            '<key name="price" generator="IntegerGenerator" min="100" max="900"/>',
            "DM218",
            "Remove generator= or min=.",
            id="forbidden-companion",
        ),
    ],
)
def test_build_remediation_names_the_attributes(tmp_path: Path, key: str, code: str, hint: str) -> None:
    result = _rejected(tmp_path, key)

    remediations = [str(item.remediation) for item in result.diagnostics if str(item.code) == code]
    assert any(text.endswith(hint) for text in remediations), remediations


def test_the_named_rule_comes_before_the_generic_parser_failure(tmp_path: Path) -> None:
    result = _rejected(tmp_path, '<key name="price" type="int" minimum="50" max="900"/>')

    assert str(result.diagnostics[0].code) == "DM103"
    assert "descriptor" in [str(item.code) for item in result.diagnostics]


def test_a_value_never_reaches_the_remediation(tmp_path: Path) -> None:
    result = _rejected(tmp_path, '<key name="price" generator="IntegerGenerator" min="12345" max="67890"/>')

    assert not any("12345" in str(item.remediation) or "67890" in item.message for item in result.diagnostics)
