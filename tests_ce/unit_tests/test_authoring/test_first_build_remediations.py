# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The first rejected Build of blind agents names the working form (campaign at 89f304b9, 50 runs). Each
descriptor is the shape an agent wrote; no remediation may echo a descriptor value."""

import json
from pathlib import Path

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ACCEPTANCE_PATH, PROJECT_ENTRY_PATH, RejectedBuild
from tests_ce.authoring_project import build_project


def _errors(tmp_path: Path, xml: str, **acceptance: object) -> list:
    result = build_project(tmp_path, xml, **acceptance)
    assert isinstance(result, RejectedBuild)
    return [item for item in result.diagnostics if item.severity == "error"]


def _raw_errors(tmp_path: Path, xml: str, expectations: list[dict[str, object]]) -> list:
    """The acceptance file as the agent wrote it, also when BuildRequestV5 refuses it."""
    (tmp_path / PROJECT_ENTRY_PATH).write_text(xml, encoding="utf-8")
    (tmp_path / PROJECT_ACCEPTANCE_PATH).parent.mkdir(parents=True, exist_ok=True)
    document = {"version": "5.0", "expectations": expectations}
    (tmp_path / PROJECT_ACCEPTANCE_PATH).write_text(json.dumps(document), encoding="utf-8")
    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()
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


def test_unique_on_a_typed_key_names_a_pool_a_key_accepts(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="tickets" count="3"><key name="ticket_id" generator="IncrementGenerator"/>'
        '<key name="title" type="string" minLength="8" maxLength="40" unique="true"/></generate></setup>'
    )

    remediations = [str(item.remediation) for item in _errors(tmp_path, xml) if str(item.code) == "DM204"]

    assert remediations and all('generator="StringGenerator" unique="true"' in text for text in remediations)


_TICKETS = (
    '<setup rngSeed="1"><generate name="tickets" count="3"><key name="ticket_id" generator="IncrementGenerator"/>'
    '<key name="price" type="int" min="1" max="9"/></generate></setup>'
)
_TICKET_ROWS = {"kind": "product", "product": "tickets"}


def test_a_foreign_key_side_without_subject_names_the_side_shape(tmp_path: Path) -> None:
    foreign_key = {
        "kind": "foreign_key",
        "child": {"product": "tickets", "field": "ticket_id"},
        "parent": {"product": "tickets", "field": "ticket_id"},
    }

    errors = _raw_errors(tmp_path, _TICKETS, [foreign_key])

    child = [str(item.remediation) for item in errors if item.path[:3] == ("expectations", 0, "foreign_key")]
    assert child and all(
        text.startswith("Put the product of child inside subject")
        or text.startswith("Put the product of parent inside subject")
        for text in child
    ), child


def test_a_row_condition_result_type_other_than_bool_says_to_omit_it(tmp_path: Path) -> None:
    condition = {"kind": "row_condition", "subject": _TICKET_ROWS, "condition": "price >= 1", "result_type": "boolean"}

    [error] = _raw_errors(tmp_path, _TICKETS, [condition])

    assert str(error.remediation).startswith('Omit result_type; "bool" is its only value.')


def test_a_row_condition_with_this_names_the_bare_field(tmp_path: Path) -> None:
    condition = {"kind": "row_condition", "subject": _TICKET_ROWS, "condition": "this.price <= 9"}

    [error] = _errors(tmp_path, _TICKETS, expectations=[condition])

    assert "bare" in str(error.remediation) and "this." in str(error.remediation)
    assert "Declare the field" not in str(error.remediation)


def test_two_keys_of_one_name_name_the_single_key_form(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="rows" count="2"><key name="n" generator="IncrementGenerator"/>'
        '<key name="f" constant="A" condition="n == 1"/><key name="f" constant="B" condition="n == 2"/>'
        "</generate></setup>"
    )

    [error] = _errors(tmp_path, xml)

    assert error.message == "Declared output fields must be unique for acceptance."
    assert "if" in str(error.remediation) and "else" in str(error.remediation)


def test_a_project_without_acceptance_file_names_the_file_to_write(tmp_path: Path) -> None:
    (tmp_path / PROJECT_ENTRY_PATH).write_text(_TICKETS, encoding="utf-8")
    result = create_authoring_application(tmp_path, descriptor_path=PROJECT_ENTRY_PATH).build()

    [error] = result.diagnostics
    assert "acceptance/build.json" in str(error.remediation) and '"version": "5.0"' in str(error.remediation)


def test_a_declared_field_named_like_a_scope_still_resolves(tmp_path: Path) -> None:
    xml = '<setup rngSeed="1"><generate name="rows" count="2"><key name="root" constant="1"/></generate></setup>'
    condition = {"kind": "row_condition", "subject": {"kind": "product", "product": "rows"}, "condition": "root == '1'"}

    result = build_project(tmp_path, xml, expectations=[condition])

    assert result.outcome == "ready", result.diagnostics


_HANDOFF = (
    '<setup rngSeed="1"><memstore id="store"/>'
    '<generate name="employments" count="4" target="store"><key name="id" generator="IncrementGenerator"/>'
    "</generate>"
    '<generate name="assignments" source="store" type="employments" distribution="ordered" count="{count}">'
    '<key name="id" script="this.id"/></generate></setup>'
)
_ROLES = [
    {"product": "employments", "field": "id", "role": {"kind": "identifier"}},
    {
        "product": "assignments",
        "field": "id",
        "role": {"kind": "foreign_key", "parent_product": "employments", "parent_field": "id"},
    },
]


def test_a_memstore_handoff_without_roles_names_its_products(tmp_path: Path) -> None:
    [error] = _errors(tmp_path, _HANDOFF.format(count=4))

    assert '"product": "employments"' in str(error.remediation)
    assert '"product": "assignments"' in str(error.remediation)
    assert "nest" in str(error.remediation)


def test_a_memstore_readback_of_a_subset_names_the_nested_form(tmp_path: Path) -> None:
    errors = _errors(tmp_path, _HANDOFF.format(count=2), product_roles=_ROLES)

    [error] = [item for item in errors if item.message.startswith("Memstore readback must preserve")]
    assert "exactly once" in str(error.remediation) and "nest" in str(error.remediation)
