# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The rejections blind agents hit most name the concrete fix, not the generic input remediation (#356 d)."""

import json
import re
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.linter import lint_source
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.build_rules import authoring_rule_catalog
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest, BuildRequestV5
from tests_ce.authoring_project import build_project

_GENERIC = next(rule.remediation for rule in authoring_rule_catalog() if rule.rule_id is AuthoringRuleId.INPUT)
_HANDOFF = (
    '<setup rngSeed="1"><memstore id="store"/>'
    '<generate name="parents" count="2" target="store"><key name="id" generator="IncrementGenerator"/></generate>'
    '<generate name="readback" source="store" type="parents" distribution="ordered">'
    '<key name="id" script="this.id"/></generate></setup>'
)
_ONE_IDENTIFIER = "Memstore readback checks one identifier role per producer"
_ADD_PRODUCER_IDENTIFIER = "Add the producer identifier role"
_ADD_CONSUMER_FK = "Add the consumer foreign-key role"
_MORE_CONSUMER_FK = "More than one foreign-key role on the consumer names this producer"
_ADD_TWO = "Add two product_roles entries"


def _first_error(result):
    return next(item for item in result.diagnostics if item.severity == "error")


def _filled(remediation: str) -> list[dict]:
    """The advertised JSON entries with placeholders replaced by names the handoff declares."""
    filled = (
        remediation.replace("<producer>", "parents")
        .replace("<consumer>", "readback")
        .replace("<field holding the key>", "id")
        .replace("<key>", "id")
    )
    return [json.loads(entry) for entry in re.findall(r'\{"product".*?\}\}', filled)]


def test_a_memstore_handoff_without_roles_names_the_role_pair(tmp_path: Path) -> None:
    diagnostic = _first_error(build_project(tmp_path, _HANDOFF))
    assert diagnostic.remediation != _GENERIC
    assert diagnostic.remediation.startswith(_ADD_TWO)
    # The advertised entries are valid product_roles declarations once the placeholders are filled in.
    entries = _filled(diagnostic.remediation)
    assert len(entries) == 2
    BuildRequestV5.model_validate({"product_roles": entries})


def test_one_identifier_without_a_readback_says_to_add_the_consumer_foreign_key(tmp_path: Path) -> None:
    roles = [{"product": "parents", "field": "id", "role": {"kind": "identifier"}}]
    diagnostic = _first_error(build_project(tmp_path, _HANDOFF, product_roles=roles))
    assert diagnostic.remediation.startswith(_ADD_CONSUMER_FK)
    entries = _filled(diagnostic.remediation)
    assert len(entries) == 1
    BuildRequestV5.model_validate({"product_roles": entries})


def test_a_foreign_key_without_a_producer_identifier_says_to_add_it(tmp_path: Path) -> None:
    roles = [
        {
            "product": "readback",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
        }
    ]
    diagnostic = _first_error(build_project(tmp_path, _HANDOFF, product_roles=roles))
    assert diagnostic.remediation.startswith(_ADD_PRODUCER_IDENTIFIER)
    entries = _filled(diagnostic.remediation)
    assert len(entries) == 1
    BuildRequestV5.model_validate({"product_roles": entries})


def test_two_foreign_keys_on_one_identifier_say_to_keep_one(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><memstore id="store"/>'
        '<generate name="parents" count="2" target="store"><key name="id" generator="IncrementGenerator"/></generate>'
        '<generate name="readback" source="store" type="parents" distribution="ordered">'
        '<key name="id" script="this.id"/><key name="parent_id" script="this.id"/></generate></setup>'
    )
    roles = [
        {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
        {
            "product": "readback",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
        },
        {
            "product": "readback",
            "field": "parent_id",
            "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
        },
    ]
    diagnostic = _first_error(build_project(tmp_path, xml, product_roles=roles))
    assert diagnostic.remediation == _MORE_CONSUMER_FK + ": keep only the one that reads the memstore back."


# A file exporter elsewhere makes DM407 require a target on the pasted readback too.
@pytest.mark.parametrize(
    "other", ["", '<generate name="report" count="1" target="JSON"><key name="id" constant="1"/></generate>']
)
def test_the_readback_that_an_unread_memstore_target_advertises_builds_ready(tmp_path: Path, other: str) -> None:
    # A scenario negative cannot paste text from a diagnostic, so this test proves the advertised copy route works.
    xml = (
        '<setup rngSeed="1"><memstore id="store"/>'
        '<generate name="parents" count="2" target="store"><key name="id" generator="IncrementGenerator"/>'
        f"</generate>{other}</setup>"
    )
    (tmp_path / "unread").mkdir()
    remediation = _first_error(build_project(tmp_path / "unread", xml)).remediation
    assert remediation != _GENERIC
    match = re.search(r'<generate name="parents_copy".*?</generate>', remediation)
    assert match is not None, remediation
    (tmp_path / "pasted").mkdir()
    pasted = xml.replace("</setup>", match.group().replace("<key>", "id") + "</setup>")
    result = build_project(tmp_path / "pasted", pasted, product_roles=_filled(remediation))
    assert result.outcome == "ready", result.diagnostics


def test_an_undeclared_expectation_field_names_the_missing_key(tmp_path: Path) -> None:
    xml = '<setup rngSeed="1"><generate name="rows" count="2"><key name="id" constant="1"/></generate></setup>'
    expectation = {"kind": "unique", "subject": {"kind": "product", "product": "rows"}, "field": "code"}
    diagnostic = _first_error(build_project(tmp_path, xml, expectations=[expectation]))
    assert diagnostic.remediation != _GENERIC
    assert "<key>" in diagnostic.remediation


def test_unknown_cardinality_names_the_count_fix(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><variable name="rows" script="[{\'id\': 1}, {\'id\': 2}]"/>'
        '<generate name="rows_out" script="rows"><key name="id" script="id"/></generate></setup>'
    )
    result = build_project(tmp_path, xml)
    messages = [item.message for item in result.diagnostics if item.severity == "error"]
    assert any("literal count" in message for message in messages), result.diagnostics


def test_an_undeclared_list_field_names_the_nested_list(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="rows" count="1"><key name="id" constant="1"/>'
        '<nestedKey name="items" type="list" count="2"><key name="sku" constant="a"/></nestedKey>'
        "</generate></setup>"
    )
    expectation = {
        "kind": "unique",
        "subject": {"kind": "product", "product": "rows", "list_field": "items"},
        "field": "code",
    }
    diagnostic = _first_error(build_project(tmp_path, xml, expectations=[expectation]))
    assert "nestedKey" in diagnostic.remediation


def test_a_duplicate_product_name_points_at_the_second_name(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><generate name="rows" count="1"><key name="id" constant="1"/></generate>'
        '<generate name="rows" count="1"><key name="id" constant="2"/></generate></setup>'
    )
    diagnostic = _first_error(build_project(tmp_path, xml))
    assert diagnostic.path == ("document", "root", "children", 1, "properties", "name")
    assert diagnostic.remediation == (
        "Rename one of the products; Build addresses every product, nested products included, by its own name."
    )


def test_a_product_name_repeated_in_a_step_points_into_the_step(tmp_path: Path) -> None:
    (tmp_path / "1_step.xml").write_text(
        '<setup><generate name="rows" count="1"><key name="id" constant="2"/></generate></setup>', encoding="utf-8"
    )
    xml = (
        '<setup rngSeed="1"><generate name="rows" count="1"><key name="id" constant="1"/></generate>'
        '<include uri="1_step.xml"/></setup>'
    )
    diagnostic = _first_error(build_project(tmp_path, xml))
    assert diagnostic.path == ("include", "1_step.xml", "root", "children", 0, "properties", "name")


def test_an_unquoted_values_list_names_the_quoted_literal_form(tmp_path: Path) -> None:
    xml = '<setup rngSeed="1"><generate name="rows" count="2"><key name="code" values="A, B" /></generate></setup>'
    expectation = {"kind": "unique", "subject": {"kind": "product", "product": "rows"}, "field": "code"}
    diagnostic = _first_error(build_project(tmp_path, xml, expectations=[expectation]))
    assert diagnostic.remediation != _GENERIC
    assert "quoted Python literals" in diagnostic.remediation


def test_dm316_no_longer_advises_cyclic_wrapping() -> None:
    xml = (
        '<setup rngSeed="1"><memstore id="mem"/>'
        '<generate name="seed" count="5" target="mem"><key name="x" constant="1"/></generate>'
        '<iterate name="reader" source="mem" type="seed" distribution="ordered" count="99" '
        'target="ConsoleExporter"/></setup>'
    )
    (finding,) = [d for d in lint_source(xml).diagnostics if d.rule == "DM316"]
    assert "Enable cyclic" not in finding.fix_hint
    assert "source size" in finding.fix_hint
    # Build proves a cyclic file source but not a cyclic memstore readback; the text must say which.
    assert "memstore readback" in finding.fix_hint


def test_two_identifier_roles_on_one_producer_name_the_extra_roles(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><memstore id="store"/>'
        '<generate name="parents" count="2" target="store"><key name="id" generator="IncrementGenerator"/>'
        '<key name="code" constant="x"/></generate>'
        '<generate name="readback" source="store" type="parents" distribution="ordered">'
        '<key name="id" script="this.id"/></generate></setup>'
    )
    roles = [
        {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
        {"product": "parents", "field": "code", "role": {"kind": "identifier"}},
        {
            "product": "readback",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
        },
    ]
    diagnostic = _first_error(build_project(tmp_path, xml, product_roles=roles))
    assert diagnostic.remediation.startswith(_ONE_IDENTIFIER)


def test_two_identifiers_and_no_foreign_key_check_one_identifier_per_producer(tmp_path: Path) -> None:
    xml = (
        '<setup rngSeed="1"><memstore id="store"/>'
        '<generate name="parents" count="2" target="store"><key name="id" generator="IncrementGenerator"/>'
        '<key name="code" constant="x"/></generate>'
        '<generate name="readback" source="store" type="parents" distribution="ordered">'
        '<key name="id" script="this.id"/></generate></setup>'
    )
    roles = [
        {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
        {"product": "parents", "field": "code", "role": {"kind": "identifier"}},
    ]
    diagnostic = _first_error(build_project(tmp_path, xml, product_roles=roles))
    assert diagnostic.remediation.startswith(_ONE_IDENTIFIER)


def test_a_policy_refusal_in_an_included_step_names_the_step(tmp_path: Path) -> None:
    (tmp_path / "descriptors").mkdir()
    (tmp_path / "descriptors" / "child.xml").write_text(
        '<setup><generate name="rows" count="1"><while condition="False"><key name="id" constant="1"/></while>'
        "</generate></setup>",
        encoding="utf-8",
    )
    workspace = AuthoringWorkspaceContext(tmp_path, PurePosixPath("descriptors/main.xml"))
    result = CeBoundedExecutor(workspace).execute(
        BoundedExecutionRequest(
            xml='<setup><include uri="child.xml"/></setup>', descriptor_path=workspace.descriptor_path, max_count=3
        )
    )
    assert [diagnostic.path for diagnostic in result.diagnostics] == [("include", "child.xml", "while")]


@pytest.mark.parametrize("count", ["", ' count="2"'])
def test_a_missing_source_in_an_included_step_names_the_step(tmp_path: Path, count: str) -> None:
    (tmp_path / "steps").mkdir()
    (tmp_path / "steps" / "a.xml").write_text(
        f'<setup><generate name="rows"{count} source="data/missing.csv"><key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    result = build_project(tmp_path, '<setup rngSeed="1"><include uri="steps/a.xml"/></setup>')
    diagnostic = _first_error(result)
    assert diagnostic.path[:2] == ("include", "steps/a.xml")
    assert str(tmp_path) not in result.model_dump_json()
