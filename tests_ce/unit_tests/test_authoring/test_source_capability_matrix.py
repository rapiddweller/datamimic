# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Runtime and authoring must project one contextual source-capability catalog."""

import pytest

from datamimic_ce.authoring.adapters.linter import lint_source
from datamimic_ce.authoring.bootstrap import create_authoring_application
from datamimic_ce.authoring.domain.requests import RunPhase, RunRequest
from datamimic_ce.engine.dsl.vocabulary.source_capabilities import (
    SourceFileFormat,
    source_capabilities,
    source_file_format_for,
)
from datamimic_ce.engine.runtime.tasks.base.task import Task
from datamimic_ce.engine.runtime.tasks.values.key_variable_task import KeyVariableTask
from datamimic_ce.engine.runtime.tasks.values.scalar.element_task import ElementTask


@pytest.mark.parametrize(
    "xml",
    (
        '<setup><generate name="rows" source="rows.csv"/></setup>',
        '<setup><iterate name="rows" source="rows.xml"/></setup>',
        '<setup><variable name="row" source="rows.json"/></setup>',
        '<setup><variable name="row" source="rows.xlsx"/></setup>',
        '<setup><variable name="row" source="rows.fcw"/></setup>',
        '<setup><generate name="rows" count="2"><variable name="row" source="[1, 2]"/></generate></setup>',
        '<setup><generate name="rows" count="2"><variable name="row" source="list(range(2))"/></generate></setup>',
        '<setup><generate name="rows" count="2"><variable name="row" source="root.runtime_rows"/></generate></setup>',
        '<setup><variable name="seed_list" script="[1, 2]"/><generate name="rows" count="1">'
        '<variable name="row" source="seed_list"/></generate></setup>',
        '<setup><generate name="rows" count="1"><nestedKey name="items" type="list" '
        'source="rows.csv"/></generate></setup>',
        '<setup><generate name="rows" count="1"><nestedKey name="items" type="list" '
        "source=\"{'data/' + 'rows.csv'}\"/></generate></setup>",
        '<setup><generate name="rows" count="1"><nestedKey name="item" type="dict" '
        'source="rows.json"/></generate></setup>',
        '<setup><generate name="rows" count="1"><key name="score" source="scores.wgt.csv"/></generate></setup>',
        '<setup><generate name="rows" count="1"><id name="score" source="scores.wgt.csv"/></generate></setup>',
        '<setup><database id="db" system="postgresql"/><generate name="rows" count="1">'
        '<reference name="customer_id" source="db" sourceType="customers" sourceKey="id"/>'
        "</generate></setup>",
    ),
)
def test_supported_source_contexts_do_not_emit_dm402(xml: str) -> None:
    assert not [diagnostic for diagnostic in lint_source(xml).diagnostics if diagnostic.rule == "DM402"]


@pytest.mark.parametrize(
    ("xml", "expected"),
    (
        ('<setup><variable name="row" source="rows.xml"/></setup>', "<variable>"),
        ('<setup><variable name="row" source="rows.dbunit.xml"/></setup>', "<variable>"),
        (
            '<setup><generate name="rows" count="1"><nestedKey name="items" type="list" '
            'source="rows.xlsx"/></generate></setup>',
            "<nestedKey>",
        ),
        (
            '<setup><generate name="rows" count="1"><nestedKey name="item" type="dict" '
            'source="rows.csv"/></generate></setup>',
            "<nestedKey>",
        ),
        (
            '<setup><generate name="rows" count="1"><key name="score" source="scores.csv"/></generate></setup>',
            "<key>",
        ),
        (
            '<setup><memstore id="mem"/><generate name="rows" count="1">'
            '<reference name="customer_id" source="mem" sourceType="customers" sourceKey="id"/>'
            "</generate></setup>",
            "<reference>",
        ),
        (
            '<setup><generate name="rows" count="1"><reference name="customer_id" '
            'source="rows.csv" sourceType="customers" sourceKey="id"/></generate></setup>',
            "<reference>",
        ),
    ),
)
def test_unsupported_source_contexts_emit_dm402(xml: str, expected: str) -> None:
    diagnostic = next(diagnostic for diagnostic in lint_source(xml).diagnostics if diagnostic.rule == "DM402")
    assert diagnostic.severity.value == "error"
    assert expected in diagnostic.message


def test_variable_xml_is_rejected_by_lint_before_runtime(tmp_path) -> None:
    result = create_authoring_application(tmp_path).dry_run(
        RunRequest(xml='<setup><variable name="row" source="rows.xml"/></setup>')
    )
    assert result.phase is RunPhase.LINT
    assert [diagnostic.code for diagnostic in result.diagnostics if diagnostic.severity == "error"] == ["DM402"]


def test_source_capabilities_project_identically_to_canonical_discovery() -> None:
    snapshot = create_authoring_application().capabilities()
    facts = source_capabilities()
    assert facts and snapshot.source_family_capabilities and snapshot.source_suffix_capabilities
    file_family = next(item for item in snapshot.source_family_capabilities if item.name == "file")
    assert {(item.element, item.source_type, item.suffixes) for item in file_family.consumers} == {
        (fact.element, fact.source_type, tuple(suffix.value for suffix in fact.file_formats))
        for fact in facts
        if fact.file_formats
    }
    for suffix in snapshot.source_suffix_capabilities:
        assert {(item.element, item.source_type) for item in suffix.consumers} == {
            (fact.element, fact.source_type)
            for fact in facts
            if any(value.value == suffix.name for value in fact.file_formats)
        }
    assert {item.name for item in snapshot.source_suffix_capabilities} == {
        suffix.value for fact in facts for suffix in fact.file_formats
    }
    for family in snapshot.source_family_capabilities:
        if family.name == "file":
            continue
        assert {(item.element, item.source_type) for item in family.consumers} == {
            (fact.element, fact.source_type)
            for fact in facts
            if (fact.allows_client if family.requires_client else fact.allows_memstore)
        }


def test_every_declared_file_capability_resolves_in_its_own_context() -> None:
    for capability in source_capabilities():
        for file_format in capability.file_formats:
            assert (
                source_file_format_for(
                    capability.element,
                    f"rows{file_format.value}",
                    capability.source_type,
                )
                is file_format
            )


def test_file_classifier_returns_canonical_enum_members() -> None:
    assert source_file_format_for("variable", "rows.wgt.ent.csv") is SourceFileFormat.WEIGHTED_ENTITY_CSV
    assert source_file_format_for("variable", "rows.wgt.csv") is SourceFileFormat.WEIGHTED_CSV


def test_element_task_satisfies_shared_task_abstraction() -> None:
    assert issubclass(KeyVariableTask, Task)
    assert issubclass(ElementTask, Task)
