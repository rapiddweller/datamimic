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


def test_an_unsupported_element_in_the_entry_is_named(tmp_path: Path) -> None:
    """#355 item 9: the refusal names the element kind, as it already does inside an included step."""
    xml = '<setup rngSeed="1"><execute type="bash">exit 0</execute><generate name="r" count="2"/></setup>'
    result = build_project(tmp_path, xml)

    assert isinstance(result, RejectedBuild)
    [refusal] = [item for item in result.diagnostics if str(item.code) == "unsupported_bounded_operation"]
    assert refusal.message == "The <execute> element has no proven bounded CE execution policy."
    assert refusal.path == ("document", "root", "children", 0)


_CALL_FORM = 'generator="IntegerGenerator(min=1, max=9)"'


@pytest.mark.parametrize(
    ("element", "code"),
    [
        pytest.param('<key name="amount" generator="IntegerGenerator" min="500" max="20000"/>', "DM214", id="key"),
        pytest.param('<key name="amount" generator="IntegerGenerator" min="500" max="20000"/>', "DM218", id="key-218"),
        pytest.param('<key name="sale" type="int" min="50" max="900" script="list_price"/>', "DM218", id="key-script"),
        pytest.param(
            '<variable name="lp" generator="IntegerGenerator" min="100" max="900"/><key name="v" script="lp"/>',
            "DM103",
            id="variable",
        ),
        pytest.param(
            '<variable name="ratio" generator="FloatGenerator" min="0.5" max="1.0"/><key name="v" script="ratio"/>',
            "DM103",
            id="variable-float",
        ),
    ],
)
def test_bounds_written_as_attributes_beside_a_generator_name_the_call_form(
    tmp_path: Path, element: str, code: str
) -> None:
    """The campaign at 89f304b9: agents read the generator parameters min and max and wrote them as attributes
    (8 of 50 first Builds). The remediation names the working form: the bounds in the generator call."""
    diagnostics = _rejected(tmp_path, element).diagnostics
    remediations = [str(item.remediation) for item in diagnostics if str(item.code) == code]

    assert any(_CALL_FORM in text for text in remediations), remediations


def test_a_bound_value_beside_a_generator_never_reaches_the_remediation(tmp_path: Path) -> None:
    result = _rejected(tmp_path, '<variable name="v" generator="IntegerGenerator" min="12345" max="67890"/>')

    assert not any("12345" in str(item.remediation) or "67890" in item.message for item in result.diagnostics)


@pytest.mark.parametrize("element", ["key", "variable"])
def test_the_generator_attribute_description_shows_the_call_form(tmp_path: Path, element: str) -> None:
    """Agents read the element capability before writing; it now shows where generator parameters go."""
    from datamimic_ce.authoring import create_authoring_application
    from datamimic_ce.authoring.domain.capabilities import CapabilityDomain

    result = create_authoring_application(tmp_path).capability(CapabilityDomain.ELEMENT, element)
    [generator] = [item for item in result.capability.attributes if item.name == "generator"]

    assert _CALL_FORM in generator.description
