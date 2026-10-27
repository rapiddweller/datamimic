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


def test_a_forbidden_dtd_keeps_the_parser_text_without_the_escape_hint(tmp_path: Path) -> None:
    xml = (
        '<?xml version="1.0"?><!DOCTYPE setup [<!ENTITY x "SECRETDTD">]><setup rngSeed="1">'
        '<generate name="a" count="1"><key name="k" constant="&x;"/></generate></setup>'
    )

    [error] = _errors(tmp_path, xml)

    assert error.message == "Descriptor failed parser validation."
    assert "&lt;" not in str(error.remediation)
    assert "SECRETDTD" not in error.model_dump_json()


def test_a_less_than_sign_in_an_included_step_names_the_escape(tmp_path: Path) -> None:
    (tmp_path / "step.xml").write_text(
        '<setup><generate name="a" count="2"><key name="k" script="7349 if 1 < 2 else 0"/></generate></setup>',
        encoding="utf-8",
    )

    [error] = _errors(tmp_path, '<setup rngSeed="1"><include uri="step.xml"/></setup>')

    assert "&lt;" in str(error.remediation) and "&amp;" in str(error.remediation)
    assert "7349" not in error.model_dump_json()


def test_unique_on_a_typed_key_names_a_pool_a_key_accepts(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="tickets" count="3"><key name="ticket_id" generator="IncrementGenerator"/>'
        '<key name="title" type="string" minLength="8" maxLength="40" unique="true"/></generate></setup>'
    )

    remediations = [str(item.remediation) for item in _errors(tmp_path, xml) if str(item.code) == "DM204"]

    assert remediations and all('generator="StringGenerator" unique="true"' in text for text in remediations)
    assert all("without unique=" in text for text in remediations)


def test_an_import_in_a_script_names_the_datetime_module_scripts_have(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="rows" count="2">'
        '<key name="d" script="__import__(\'datetime\').date(2026, 1, 1)"/></generate></setup>'
    )

    [remediation] = [str(item.remediation) for item in _errors(tmp_path, xml) if str(item.code) == "DM314"]

    assert "datetime.date(" in remediation and "import.field" not in remediation


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


def test_a_field_typo_in_a_foreign_key_side_with_a_subject_gets_the_shape_only(tmp_path: Path) -> None:
    foreign_key = {
        "kind": "foreign_key",
        "child": {"subject": _TICKET_ROWS, "fields": "ticket_id"},
        "parent": {"subject": _TICKET_ROWS, "field": "ticket_id"},
    }

    errors = _raw_errors(tmp_path, _TICKETS, [foreign_key])

    assert errors and not any("Put the product" in str(item.remediation) for item in errors)
    assert all("A foreign_key expectation has this shape" in str(item.remediation) for item in errors)


def test_a_row_condition_result_type_other_than_bool_says_to_omit_it(tmp_path: Path) -> None:
    condition = {"kind": "row_condition", "subject": _TICKET_ROWS, "condition": "price >= 1", "result_type": "int"}

    [error] = _raw_errors(tmp_path, _TICKETS, [condition])

    assert str(error.remediation).startswith("Omit result_type: a row condition is always boolean.")


def test_result_type_boolean_and_range_min_max_are_ready_on_the_first_build(tmp_path: Path) -> None:
    """sonnet e05-2 wrote result_type "boolean"; 8 of 50 first Builds wrote min and max."""
    condition = {"kind": "row_condition", "subject": _TICKET_ROWS, "condition": "price >= 1", "result_type": "boolean"}
    bounds = {"kind": "range", "subject": _TICKET_ROWS, "field": "price", "min": 1, "max": 9}

    result = build_project(tmp_path, _TICKETS, expectations=[condition, bounds])

    assert result.outcome == "ready", result.diagnostics


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


def test_a_child_without_a_parent_copy_names_the_grouping_key(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="depots" count="2"><key name="depot_id" generator="IncrementGenerator"/>'
        '<generate name="slots" count="2"><key name="depot_id" script="depot_id"/></generate></generate></setup>'
    )
    count = {
        "kind": "per_parent_count",
        "subject": {"kind": "per_parent", "parent_product": "depots", "child_product": "slots"},
        "count": 2,
    }

    errors = [item for item in _errors(tmp_path, xml, expectations=[count]) if item.message.startswith("could not")]

    assert errors and all('script="parent.' in str(error.remediation) for error in errors)


def test_a_distribution_on_a_weighted_key_says_the_file_weights_apply(tmp_path: Path) -> None:
    (tmp_path / "functions.wgt.csv").write_text("OPERATOR|80\nPLANNER|20\n", encoding="utf-8")
    xml = (
        '<setup rngSeed="1"><generate name="rows" count="2">'
        '<key name="function" source="functions.wgt.csv" distribution="weighted"/></generate></setup>'
    )

    remediations = [str(item.remediation) for item in _errors(tmp_path, xml) if str(item.code) == "DM105"]

    assert remediations and all("remove distribution=" in text for text in remediations), remediations


def test_a_per_parent_count_with_parent_and_child_sides_names_the_subject(tmp_path: Path) -> None:
    count = {
        "kind": "per_parent_count",
        "parent": {"product": "tickets", "field": "ticket_id"},
        "child": {"product": "tickets", "field": "ticket_id"},
        "count": 3,
    }

    errors = _raw_errors(tmp_path, _TICKETS, [count])

    assert errors and all(str(item.remediation).startswith("Put both products inside subject") for item in errors)
    assert all("nested <generate>" in str(item.remediation) for item in errors)


def test_a_per_parent_count_with_grouping_fields_says_that_the_nesting_groups(tmp_path: Path) -> None:
    """haiku e02-1 named the products as sides and the grouping key in child_field and parent_field."""
    count = {
        "kind": "per_parent_count",
        "parent": {"kind": "product", "product": "tickets"},
        "child": {"kind": "product", "product": "tickets"},
        "child_field": "ticket_id",
        "parent_field": "ticket_id",
        "count": 3,
    }

    errors = _raw_errors(tmp_path, _TICKETS, [count])

    fields = [str(item.remediation) for item in errors if item.path[3:] in (("child_field",), ("parent_field",))]
    assert len(fields) == 2 and all("grouped by that nesting" in text for text in fields), fields
