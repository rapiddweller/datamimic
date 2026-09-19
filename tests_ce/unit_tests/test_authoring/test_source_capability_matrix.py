# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Runtime and authoring must project one contextual source-capability catalog."""

import inspect

import pytest

from datamimic_ce.authoring.contracts import AuthoringStage
from datamimic_ce.authoring.dryrun import dry_run_source
from datamimic_ce.authoring.linter import lint_source
from datamimic_ce.authoring.reference import capabilities_manifest, distributions_reference
from datamimic_ce.model.constraints import (
    SourceFileFormat,
    serialize_source_capability,
    source_capabilities,
    source_file_format_for,
)
from datamimic_ce.tasks.element_task import ElementTask
from datamimic_ce.tasks.key_variable_task import KeyVariableTask
from datamimic_ce.tasks.task import Task


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


def test_variable_xml_is_rejected_by_lint_before_runtime() -> None:
    result = dry_run_source('<setup><variable name="row" source="rows.xml"/></setup>')
    assert result.stage is AuthoringStage.LINT
    assert [diagnostic.rule for diagnostic in result.diagnostics if diagnostic.severity.value == "error"] == ["DM402"]


def test_source_capabilities_project_identically_to_manifest_and_reference() -> None:
    expected = [serialize_source_capability(capability) for capability in source_capabilities()]
    assert capabilities_manifest()["source_capabilities"] == expected
    prose = distributions_reference()
    for capability in source_capabilities():
        assert f"<{capability.element}>" in prose
        for file_format in capability.file_formats:
            assert file_format.value in prose


def test_datasource_registry_is_the_runtime_source_boundary() -> None:
    from datamimic_ce.data_sources import data_source_registry
    from datamimic_ce.tasks import nested_key_task, reference_task, task_util, variable_task

    registry_source = inspect.getsource(data_source_registry)
    assert "source_file_format_for" in registry_source
    for routing_api in (
        "load_generate_source",
        "plan_variable_source",
        "load_nested_key_source",
        "load_reference_source",
    ):
        assert routing_api in registry_source

    forbidden_task_details = (
        "source_file_format_for",
        "SourceFileFormat",
        "FileUtil",
        "RdbmsClient",
        "MongoDBClient",
        "SourceDistribution",
        "get_distributed_data",
        "get_unique_data",
        "get_cyclic_data_list",
    )
    for module in (nested_key_task, reference_task, task_util, variable_task):
        task_source = inspect.getsource(module)
        for detail in forbidden_task_details:
            assert detail not in task_source, f"{module.__name__} leaks datasource detail {detail}"


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


def test_element_task_satisfies_shared_task_abstraction() -> None:
    assert issubclass(KeyVariableTask, Task)
    assert issubclass(ElementTask, Task)
