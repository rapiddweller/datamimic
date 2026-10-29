# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Public discovery projects the actual CE registry and canonical request contracts."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain, CapabilityNotFound, DslCatalogSnapshot
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1, DmJsonNodeV1
from datamimic_ce.authoring.domain.reference import ReferenceResult
from datamimic_ce.authoring.domain.requests import AuthoringSchemaId, BuildRequestV5, ReferenceRequest, ReferenceTopic
from datamimic_ce.authoring.domain.schema import build_schema_index
from datamimic_ce.engine.dsl.model.registry import canonical_tag, get_element_definition, list_element_tags
from datamimic_ce.engine.dsl.vocabulary.enums.converter_enums import ConverterEnum
from datamimic_ce.engine.io.api import buffered_exporter_names
from datamimic_ce.errors import ATTRIBUTE_ESCAPE, SCRIPT_IMPORT_FIX
from datamimic_ce.interfaces.cli import app
from tests_ce.authoring_project import build_project


@pytest.fixture(scope="module")
def application():
    return create_authoring_application()


def test_overview_addresses_every_current_topic(application):
    result = application.reference(ReferenceRequest(topic=ReferenceTopic.OVERVIEW))
    assert "DM JSON" in result.content and "Build" in result.content
    assert set(result.next_topics) == set(ReferenceTopic) - {ReferenceTopic.OVERVIEW}
    assert ReferenceResult.model_validate_json(result.model_dump_json()) == result


def test_schema_discovery_uses_actual_closed_dm_json_and_build_models(application):
    assert application.schema(AuthoringSchemaId.DM_JSON_DOCUMENT_V1) == application.document_schema()
    build = application.schema(AuthoringSchemaId.BUILD_REQUEST_V5)
    assert build["title"] == "BuildRequestV5" and build["additionalProperties"] is False
    assert set(build["properties"]) == set(BuildRequestV5.model_fields)
    for schema_id in AuthoringSchemaId:
        assert application.schema(schema_id)


def test_advertised_row_condition_examples_evaluate_against_data(application):
    from datamimic_ce.authoring.domain.row_conditions import evaluate_row_condition

    schema = application.schema(AuthoringSchemaId.BUILD_REQUEST_V5)
    examples = schema["$defs"]["RowConditionExpectation"]["properties"]["condition"]["examples"]
    assert examples
    for expression in examples:
        assert evaluate_row_condition(expression, {"amount": 25, "addresses": [{"id": 1}, {"id": 2}]})


def test_capability_keeps_the_owners_executable_literal_examples(application):
    from datamimic_ce.engine.dsl.vocabulary.value_literals import parse_literal_values

    capability = application.capability(CapabilityDomain.ELEMENT, "key").capability
    examples = capability.properties_schema["properties"]["values"]["examples"]
    assert examples == get_element_definition("key").model.model_fields["values"].examples
    for example in examples:
        assert parse_literal_values(example)


def test_converters_and_targets_come_from_current_owners(application):
    assert set(application.capability_names(CapabilityDomain.CONVERTER)) == {member.value for member in ConverterEnum}
    snapshot = application.capabilities()
    assert {
        item.name for item in snapshot.exporter_capabilities if item.output_kind == "file"
    } == buffered_exporter_names()


def test_execute_target_capability_uses_model_description(application):
    result = application.capability(CapabilityDomain.ELEMENT, "execute")
    assert result.ok
    target = next(field for field in result.capability.attributes if field.name == "target")
    assert target.description == get_element_definition("execute").model.model_fields["target"].description
    assert "execute_sql_script" in target.description


def test_element_lookup_is_closed_and_registry_derived(application):
    names = application.capability_names(CapabilityDomain.ELEMENT)
    assert names and set(names) == {canonical_tag(tag) for tag in list_element_tags()}
    for name in names:
        result = application.capability(CapabilityDomain.ELEMENT, name)
        assert result.ok and result.capability.properties_schema
        definition = get_element_definition(name)
        assert result.capability.aliases == tuple(sorted(definition.aliases))
        assert result.capability.content_modes == definition.content_modes
        assert result.capability.bounded_execution == definition.bounded_execution_profile
    missing = application.capability(CapabilityDomain.ELEMENT, "generat")
    assert isinstance(missing, CapabilityNotFound)
    assert missing.available_names == names


def test_schema_index_covers_all_runtime_tags_including_aliases():
    tags = list_element_tags()
    assert tags and set(tags) == set(build_schema_index().tags)


def test_compact_names_match_every_full_capability_without_truncation(application):
    snapshot = application.capabilities()
    compact = snapshot.to_index_dict()
    assert set(compact) == {domain.value for domain in CapabilityDomain}
    for domain in CapabilityDomain:
        names = application.capability_names(domain)
        assert names and compact[domain.value] == list(names)
        assert len(names) == len(set(names))
        for name in names:
            detail = application.capability(domain, name)
            assert detail.ok and detail.name == name
    assert DslCatalogSnapshot.model_validate_json(snapshot.model_dump_json()) == snapshot


def test_compact_budget_remains_bounded(application):
    compact_bytes = len(json.dumps(application.capabilities().to_index_dict()).encode())
    full_bytes = len(application.capabilities().model_dump_json().encode())
    assert compact_bytes < 25_000
    assert compact_bytes <= full_bytes * 0.20


def test_generator_names_are_complete_and_deterministic(application):
    names = application.capability_names(CapabilityDomain.GENERATOR)
    assert names and "SequenceTableGenerator" in names
    assert names == application.capability_names(CapabilityDomain.GENERATOR)
    result = application.capability(CapabilityDomain.GENERATOR, "SequenceTableGenerator")
    assert result.ok and "sequence" in result.capability.parameters


def test_reference_names_are_addressable_and_no_other_entry_substitutes(application):
    for topic in ReferenceTopic:
        names = application.reference_names(topic)
        for name in names:
            result = application.reference(ReferenceRequest(topic=topic, name=name))
            if result.rules is not None:
                assert tuple(str(rule.rule_id) for rule in result.rules) == (name,)
            else:
                assert tuple(entry.name for entry in result.entries) == (name,)


def test_cli_compact_and_full_match_public_application(application):
    runner = CliRunner()
    compact = runner.invoke(app, ["authoring", "capabilities"])
    full = runner.invoke(app, ["authoring", "capabilities", "--full"])
    assert compact.exit_code == full.exit_code == 0
    assert json.loads(compact.stdout) == application.capabilities().to_index_dict()
    assert json.loads(full.stdout) == application.capabilities().to_dict()


def test_cli_capability_unknown_name_is_machine_readable(application):
    result = CliRunner().invoke(app, ["authoring", "capability", "--domain", "element", "--name", "bogus"])
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["ok"] is False and data["error"] == "capability_not_found"
    assert data["available_names"] == list(application.capability_names(CapabilityDomain.ELEMENT))


def test_cli_rejects_unknown_domain_without_partial_result():
    result = CliRunner().invoke(app, ["authoring", "capability", "--domain", "bogus", "--name", "generate"])
    assert result.exit_code != 0


def test_cli_reference_is_exact_typed_payload(application):
    result = CliRunner().invoke(app, ["authoring", "reference", "--topic", "rules", "--name", "DM401"])
    assert result.exit_code == 0
    expected = application.reference(ReferenceRequest(topic=ReferenceTopic.RULES, name="DM401"))
    assert ReferenceResult.model_validate_json(result.stdout) == expected
    assert expected.rules and len(expected.rules) == 1


def test_learning_retains_correct_scope_and_timeseries_guidance(application):
    context = application.reference(ReferenceRequest(topic=ReferenceTopic.LEARNING, name="context"))
    description = context.entries[0].description
    assert all(alias in description for alias in ("this.field", "parent.field", "root.field"))
    assert "Current-scope fields can resolve bare" in description
    assert "outermost bare name wins" in description
    series = application.reference(ReferenceRequest(topic=ReferenceTopic.LEARNING, name="timeseries"))
    description = series.entries[0].description
    assert all(field in description for field in ("ts.now", "ts.step", "ts.series"))
    assert "default 1" in description and "floor((end-start)/interval)" in description
    assert "rng_seed" in description
    from datamimic_ce.engine.dsl.model.generation.timeseries import TimeSeriesConfig

    window = TimeSeriesConfig.parse("2026-01-01T00:00:00", "2026-01-01T02:30:00", "PT1H")
    assert window.ticks_per_series == 2
    assert [(window.at(i).step, window.at(i).series) for i in range(4)] == [(0, 0), (1, 0), (0, 1), (1, 1)]


@pytest.mark.parametrize("element, family", [("database", "db"), ("mongodb", "mongo")])
def test_connection_catalog_preserves_profile_precedence_and_read_only_contract(application, element, family):
    result = application.capability(CapabilityDomain.ELEMENT, element)
    assert result.ok
    attributes = {field.name: field for field in result.capability.attributes}
    host = attributes["host"].description
    assert f"'{{system}}.{family}.host'" in host
    assert "overrides this attribute" in host and "this value is kept" in host
    assert attributes["read_only"].xml_name == "readOnly"
    properties = result.capability.properties_schema["properties"]
    assert properties["host"]["description"] == host
    assert properties["read_only"]["type"] == "boolean"


def test_learning_names_the_project_data_file_forms_the_s24_scenario_proves(application):
    """Blind agents typed the names of a weighted file into the project instead of reading it (campaign at
    89f304b9, e06). The forms named here are the ones tests_ce/scenarios/s24_project_data_files builds."""
    [entry] = application.reference(ReferenceRequest(topic=ReferenceTopic.LEARNING, name="data_files")).entries
    text = entry.description
    for form in (
        '<key name="function" source="fixtures/functions.wgt.csv"/>',
        '<variable name="row" source="fixtures/people.ent.csv" distribution="ordered"/>',
        "int(row.age)",
        ".wgt.ent.csv",
        'separator=","',
    ):
        assert form in text, form
    assert 'distribution="ordered" has no effect on a .wgt.ent.csv <variable>' in text
    # file_sources owns the where=/columns= rules; data_files only points to it.
    assert "--topic learning --name file_sources" in text
    assert 'where="' not in text and 'columns="' not in text
    assert entry.path == "tests_ce/scenarios/s24_project_data_files"
    overview = application.reference(ReferenceRequest(topic=ReferenceTopic.OVERVIEW))
    assert "--topic learning --name data_files" in overview.content


def test_learning_lookup_teaches_the_join_the_s31_scenario_builds(application):
    """Blind agents found no way to join a second file and tried open(), <variable where=> and nested
    generates (campaign b3 at 57db8b06, e07). The reference text must stay the form that s31 builds."""
    [entry] = application.reference(ReferenceRequest(topic=ReferenceTopic.LEARNING, name="lookup")).entries
    assert entry.path == "tests_ce/scenarios/s31_file_lookup"
    scenario = (Path(__file__).parents[3] / entry.path / "datamimic.xml").read_text(encoding="utf-8")
    for form in (
        '<variable name="branches" source="data/entity/branches.ent.csv" storage="data" distribution="ordered"/>',
        '<variable name="branch" script="{b.branch_id: b for b in branches}.get(branch_id)"/>',
        "branch.city if branch else 'UNKNOWN'",
    ):
        assert form in entry.description and form in scenario, form
    for name in ("file_sources", "data_files"):
        [pointer] = application.reference(ReferenceRequest(topic=ReferenceTopic.LEARNING, name=name)).entries
        assert "--topic learning --name lookup" in pointer.description, name
    overview = application.reference(ReferenceRequest(topic=ReferenceTopic.OVERVIEW))
    assert "--topic learning --name lookup" in overview.content


def test_overview_shows_the_script_fix_and_scopes_the_escape_to_xml(application):
    """Agents read the overview before their first Build. The reference holds no descriptor, so this is a Python
    test; s33 refuses __import__ and a raw < in XML with these texts."""
    overview = application.reference(ReferenceRequest(topic=ReferenceTopic.OVERVIEW)).content
    assert SCRIPT_IMPORT_FIX in overview
    assert f"In an XML file: {ATTRIBUTE_ESCAPE}; DM JSON takes a raw <." in overview


@pytest.mark.parametrize(("script", "outcome"), [("a <= 2", "ready"), ("a &lt;= 2", "rejected")])
def test_dm_json_takes_a_raw_less_than(tmp_path, script, outcome):
    """Compile escapes a DM JSON value, so the XML escape applied in DM JSON is escaped twice and fails."""
    document = DmJsonDocumentV1(
        root=DmJsonNodeV1(
            kind="setup",
            properties={"rng_seed": 1},
            children=(
                DmJsonNodeV1(
                    kind="generate",
                    properties={"name": "t", "count": "3"},
                    children=(
                        DmJsonNodeV1(kind="key", properties={"name": "a", "generator": "IncrementGenerator"}),
                        DmJsonNodeV1(kind="key", properties={"name": "b", "script": script}),
                    ),
                ),
            ),
        )
    )
    built = build_project(
        tmp_path,
        document,
        version="5.0",
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "t"}, "count": 3}],
    )
    assert built.outcome == outcome


def test_authoring_help_points_to_the_data_file_guidance():
    result = CliRunner().invoke(app, ["authoring", "--help"])

    assert result.exit_code == 0
    assert "data_files" in result.stdout
