# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The first rejected Build of blind agents names the working form (campaign at 89f304b9, 50 runs). Each
descriptor is the shape an agent wrote; no remediation may echo a descriptor value."""

from pathlib import Path

from datamimic_ce.authoring.domain.requests import RejectedBuild
from tests_ce.authoring_project import build_project


def _errors(tmp_path: Path, xml: str, **acceptance: object) -> list:
    result = build_project(tmp_path, xml, **acceptance)
    assert isinstance(result, RejectedBuild)
    return [item for item in result.diagnostics if item.severity == "error"]


def test_a_less_than_sign_in_an_attribute_names_the_escape(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="rows" count="2"><key name="n" generator="IncrementGenerator"/>\n'
        '<key name="m" script="n if n <= 20 else 7349"/></generate></setup>'
    )

    [error] = _errors(tmp_path, xml)

    assert error.message == "Descriptor is not well-formed XML."
    assert error.path == ("descriptor", "datamimic.xml", "line", 2)
    assert "&lt;" in str(error.remediation) and "&amp;" in str(error.remediation)
    assert "7349" not in str(error.remediation)


def test_an_unclosed_element_gets_the_same_well_formed_diagnostic(tmp_path: Path) -> None:
    xml = '<setup rngSeed="1"><generate name="rows" count="2"><key name="n" constant="1"></generate></setup>'

    [error] = _errors(tmp_path, xml)

    assert error.message == "Descriptor is not well-formed XML."
