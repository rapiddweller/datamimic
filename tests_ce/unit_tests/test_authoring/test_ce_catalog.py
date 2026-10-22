from pathlib import Path
from unittest.mock import Mock

from pydantic import TypeAdapter

from datamimic_ce.authoring.adapters.catalog import CeDslCatalog
from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.capabilities import (
    CapabilityDomain,
    CapabilityFound,
    CapabilityLookupResult,
    CapabilityNotFound,
)
from datamimic_ce.authoring.domain.reference import AuthoringExampleReference, ProjectStarter
from datamimic_ce.authoring.domain.requests import BuildResult, ReferenceRequest, ReferenceTopic
from tests_ce.authoring_project import build_project


def _build_starter(project: Path, starter: ProjectStarter) -> BuildResult:
    project.mkdir(exist_ok=True)
    return build_project(project, starter.entry_xml, **starter.acceptance.model_dump())


def test_snapshot_is_lazy_and_ce_only():
    codec = Mock(wraps=CeDmJsonCodec())
    catalog = CeDslCatalog(codec)
    assert not codec.document_schema.called
    snapshot = catalog.snapshot()
    assert catalog.snapshot() is snapshot
    assert codec.document_schema.call_count == 1
    assert not codec.compile.called
    assert snapshot.capability_names(CapabilityDomain.SOURCE_DISTRIBUTION) == ("cumulated", "ordered", "random")
    assert "kafka" not in snapshot.capability_names(CapabilityDomain.ELEMENT)
    assert snapshot.capability_names(CapabilityDomain.SOURCE_FAMILY) == ("database", "file", "memstore", "mongodb")
    found = snapshot.capability(CapabilityDomain.GENERATOR, "IncrementGenerator")
    assert isinstance(found, CapabilityFound)
    assert TypeAdapter(CapabilityLookupResult).validate_json(found.model_dump_json()) == found
    assert isinstance(snapshot.capability(CapabilityDomain.ELEMENT, "kafka"), CapabilityNotFound)


def test_listing_examples_does_not_compile_other_branches():
    codec = Mock(wraps=CeDmJsonCodec())
    catalog = CeDslCatalog(codec)
    listing = catalog.reference(ReferenceRequest(topic=ReferenceTopic.EXAMPLES))
    assert listing.entries and all(
        isinstance(entry, AuthoringExampleReference) and entry.project is None for entry in listing.entries
    )
    assert not codec.compile.called
    result = catalog.reference(ReferenceRequest(topic=ReferenceTopic.EXAMPLES, name="starter"))
    assert codec.compile.call_count == 1
    (example,) = result.entries
    assert isinstance(example, AuthoringExampleReference) and example.project is not None
    assert example.project.entry_xml
    assert example.verification == "not_executed"


def test_reference_topics_are_typed():
    catalog = CeDslCatalog(CeDmJsonCodec())
    for topic in ReferenceTopic:
        result = catalog.reference(ReferenceRequest(topic=topic))
        assert result.topic == topic
        assert result.content
        assert result.model_dump_json()
    assert catalog.reference(ReferenceRequest(topic=ReferenceTopic.EXPECTATIONS, name="exact_count")).entries


def test_snapshot_updates_after_registry_extension():
    from pydantic import BaseModel

    from datamimic_ce.engine.dsl.model.registry import (
        ElementDefinition,
        register_element_extension,
        unregister_element_extension,
    )

    class ExtensionModel(BaseModel):
        label: str

    catalog = CeDslCatalog(CeDmJsonCodec())
    before = catalog.snapshot()
    register_element_extension(ElementDefinition("catalog-extension", ExtensionModel, None))
    try:
        after = catalog.snapshot()
        assert after is not before
        found = after.capability(CapabilityDomain.ELEMENT, "catalog-extension")
        assert found.ok
        assert found.capability.attributes[0].name == "label"
        assert found.capability.bounded_execution.strategy == "unsupported"
    finally:
        unregister_element_extension("catalog-extension")
    assert "catalog-extension" not in catalog.snapshot().capability_names(CapabilityDomain.ELEMENT)


def test_discovery_matches_runtime_owners():
    from datamimic_ce.domains.api import iter_generator_capabilities as domain_generators
    from datamimic_ce.engine.dsl.api import ConverterEnum, NumberDistribution
    from datamimic_ce.engine.io.api import buffered_exporter_names
    from datamimic_ce.engine.runtime.api import iter_generator_capabilities as runtime_generators

    snapshot = CeDslCatalog(CeDmJsonCodec()).snapshot()
    assert set(snapshot.capability_names(CapabilityDomain.GENERATOR)) == {
        value.name for value in (*domain_generators(), *runtime_generators())
    }
    assert set(snapshot.capability_names(CapabilityDomain.CONVERTER)) == {value.value for value in ConverterEnum}
    assert set(snapshot.capability_names(CapabilityDomain.NUMERIC_DISTRIBUTION)) == {
        value.value for value in NumberDistribution
    }
    assert {
        value.name for value in snapshot.exporter_capabilities if value.output_kind == "file"
    } == buffered_exporter_names()


def test_memstore_example_compiles_only_requested_branch():
    codec = Mock(wraps=CeDmJsonCodec())
    result = CeDslCatalog(codec).reference(ReferenceRequest(topic=ReferenceTopic.EXAMPLES, name="memstore"))
    assert codec.compile.call_count == 1
    (example,) = result.entries
    assert isinstance(example, AuthoringExampleReference) and example.project is not None
    assert len(example.project.acceptance.expectations) == 2
    assert 'sourceEntity="rows"' in example.project.entry_xml


def test_unknown_named_reference_does_not_return_another_entry():
    catalog = CeDslCatalog(CeDmJsonCodec())
    for topic in (
        ReferenceTopic.ASSEMBLY,
        ReferenceTopic.EXAMPLES,
        ReferenceTopic.EXPECTATIONS,
        ReferenceTopic.LEARNING,
    ):
        result = catalog.reference(ReferenceRequest(topic=topic, name="missing"))
        assert result.entries == ()


def test_every_published_self_contained_example_builds(tmp_path):
    from datamimic_ce.authoring import create_authoring_application
    from datamimic_ce.authoring.domain.requests import ReadyBuild

    application = create_authoring_application(workspace_root=tmp_path)
    listing = application.reference(ReferenceRequest(topic=ReferenceTopic.EXAMPLES))
    assert listing.entries
    for entry in listing.entries:
        (example,) = application.reference(ReferenceRequest(topic=ReferenceTopic.EXAMPLES, name=entry.name)).entries
        assert isinstance(example, AuthoringExampleReference) and example.project is not None
        result = _build_starter(tmp_path / entry.name, example.project)
        assert isinstance(result, ReadyBuild), (entry.name, result)


def test_guide_reference_query_returns_buildable_assembly(tmp_path):
    import json
    import re

    from typer.testing import CliRunner

    from datamimic_ce.authoring.domain.requests import ReadyBuild
    from datamimic_ce.interfaces.cli import app

    guide = (Path(__file__).parents[3] / "AGENTS.md").read_text()
    command = re.search(r"`datamimic (authoring reference --topic assembly --name [a-z]+)`", guide)
    assert command is not None
    response = CliRunner().invoke(app, command[1].split())
    assert response.exit_code == 0, response.stdout

    payload = json.loads(response.stdout)
    assert payload["entries"]
    starter = ProjectStarter.model_validate(payload["entries"][0]["starter"])
    assert isinstance(_build_starter(tmp_path, starter), ReadyBuild)
