# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Lazy CE catalog projection; declarations never claim execution or delivery."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import JsonValue, TypeAdapter

from datamimic_ce.authoring.domain.build_rules import authoring_rule_catalog
from datamimic_ce.authoring.domain.capabilities import (
    AttributeCapability,
    AuthoringElementCapability,
    ConverterCapability,
    DslCatalogSnapshot,
    ElementPropertyCapability,
    EntityCapability,
    ExporterTargetCapability,
    GeneratorCapability,
    NumericDistributionCapability,
    SourceConsumerCapability,
    SourceDistributionCapability,
    SourceFamilyCapability,
    SourceSuffixCapability,
    TargetFamilyCapability,
)
from datamimic_ce.authoring.domain.diagnostics import RuleCatalogEntry, RuleOwner
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1, DmJsonNodeV1
from datamimic_ce.authoring.domain.expectations import ExactCountExpectation, ExpectationIntent, ProductRowsSubject
from datamimic_ce.authoring.domain.proof import ForeignKeyRole, IdentifierRole, ProductRoleDeclaration
from datamimic_ce.authoring.domain.reference import (
    AuthoringAssemblyReference,
    AuthoringExampleReference,
    AuthoringLearningReference,
    AuthoringVariantReference,
    ProjectStarter,
    ReferenceResult,
)
from datamimic_ce.authoring.domain.requests import BuildRequestV5, ReferenceRequest, ReferenceTopic

if TYPE_CHECKING:
    from datamimic_ce.authoring.ports import DmJsonDescriptorContract
    from datamimic_ce.domains.domain_core.contracts.attribute_catalog import FieldSpec


_JSON_OBJECT = TypeAdapter(dict[str, JsonValue])


class CeDslCatalog:
    def __init__(self, descriptor_contract: DmJsonDescriptorContract) -> None:
        self._codec = descriptor_contract
        self._snapshot: DslCatalogSnapshot | None = None
        self._revision: tuple[int, int] | None = None

    def snapshot(self) -> DslCatalogSnapshot:
        from datamimic_ce.engine.dsl.api import registry_revision, rule_registry_revision

        revision = (registry_revision(), rule_registry_revision())
        if self._snapshot is None or revision != self._revision:
            self._snapshot = self._build_snapshot()
            self._revision = revision
        return self._snapshot

    def _build_snapshot(self) -> DslCatalogSnapshot:
        from datamimic_ce.domains.api import iter_generator_capabilities as domain_generators
        from datamimic_ce.domains.api import list_entity_specs
        from datamimic_ce.engine.dsl.api import (
            EL_MONGODB,
            EXPORTER_CONSOLE_EXPORTER,
            EXPORTER_LOG_EXPORTER,
            EXPORTER_TEST_RESULT_EXPORTER,
            POSITIONAL_NUMBER_SEQUENCES,
            ConverterEnum,
            ExportOperation,
            NumberDistribution,
            SourceDistribution,
            canonical_tag,
            get_element_definition,
            list_element_tags,
            source_capabilities,
        )
        from datamimic_ce.engine.io.api import buffered_exporter_names
        from datamimic_ce.engine.runtime.api import iter_generator_capabilities

        schema = _JSON_OBJECT.validate_python(self._codec.document_schema())
        definitions = _JSON_OBJECT.validate_python(schema["$defs"])
        union = _JSON_OBJECT.validate_python(definitions["DmJsonNodeV1"])
        discriminator = _JSON_OBJECT.validate_python(union["discriminator"])
        mapping = TypeAdapter(dict[str, str]).validate_python(discriminator["mapping"])
        elements = []
        for tag in sorted({canonical_tag(tag) for tag in list_element_tags()}):
            definition = get_element_definition(tag)
            assert definition is not None
            fields = definition.model.model_fields if definition.model is not None else {}
            content_attributes = {name for mode in definition.content_modes for name in mode.required_attributes}
            node_schema = _JSON_OBJECT.validate_python(definitions[mapping[tag].removeprefix("#/$defs/")])
            node_properties = _JSON_OBJECT.validate_python(node_schema["properties"])
            elements.append(
                AuthoringElementCapability(
                    name=tag,
                    aliases=tuple(sorted(definition.aliases)),
                    attributes=tuple(
                        ElementPropertyCapability(
                            name=name,
                            xml_name=field.alias or name,
                            required=field.is_required(),
                            description=field.description or "",
                        )
                        for name, field in fields.items()
                        if name not in content_attributes and field.alias not in content_attributes
                    ),
                    children=tuple(sorted({canonical_tag(child) for child in definition.allowed_children}))
                    if definition.allowed_children is not None
                    else None,
                    singleton_children=tuple(sorted(definition.singleton_children)),
                    content_modes=definition.content_modes,
                    bounded_execution=definition.bounded_execution_profile,
                    properties_schema=_JSON_OBJECT.validate_python(node_properties["properties"]),
                )
            )
        source_facts = source_capabilities()
        suffixes = sorted({suffix.value for fact in source_facts for suffix in fact.file_formats})
        sources = []
        targets = []
        for element in elements:
            definition = get_element_definition(element.name)
            assert definition is not None
            if definition.client_family or definition.memory_store:
                sources.append(
                    SourceFamilyCapability(
                        name=element.name,
                        requires_client=definition.client_family,
                        consumers=tuple(
                            SourceConsumerCapability(element=fact.element, source_type=fact.source_type)
                            for fact in source_facts
                            if (fact.allows_client if definition.client_family else fact.allows_memstore)
                        ),
                    )
                )
                targets.append(
                    TargetFamilyCapability(
                        name=element.name,
                        requires_client=definition.client_family,
                        operations=(
                            "insert",
                            *(
                                operation.value
                                for operation in (
                                    ExportOperation.for_mongodb()
                                    if element.name == EL_MONGODB
                                    else ExportOperation.for_rdbms()
                                )
                            ),
                        )
                        if definition.client_family
                        else ("insert",),
                    )
                )
        sources.append(
            SourceFamilyCapability(
                name="file",
                requires_client=False,
                consumers=tuple(
                    SourceConsumerCapability(
                        element=fact.element,
                        source_type=fact.source_type,
                        suffixes=tuple(suffix.value for suffix in fact.file_formats),
                    )
                    for fact in source_facts
                    if fact.file_formats
                ),
            )
        )
        file_exporters = tuple(sorted(buffered_exporter_names()))
        targets.append(TargetFamilyCapability(name="file", requires_client=False, operations=("write",)))
        exporters = tuple(ExporterTargetCapability(name=name, output_kind="file") for name in file_exporters)
        exporters += tuple(
            ExporterTargetCapability(name=name, output_kind="diagnostic")
            for name in sorted((EXPORTER_CONSOLE_EXPORTER, EXPORTER_LOG_EXPORTER, EXPORTER_TEST_RESULT_EXPORTER))
        )
        source_distributions: tuple[SourceDistribution, ...] = tuple(SourceDistribution)
        numeric_distributions: tuple[NumberDistribution, ...] = tuple(NumberDistribution)
        return DslCatalogSnapshot(
            element_capabilities=tuple(elements),
            generator_capabilities=tuple(
                GeneratorCapability(name=item.name, parameters=item.parameters)
                for item in sorted((*domain_generators(), *iter_generator_capabilities()), key=lambda item: item.name)
            ),
            converter_capabilities=tuple(
                ConverterCapability(name=item.value) for item in sorted(ConverterEnum, key=lambda item: item.value)
            ),
            entities=tuple(
                EntityCapability(
                    name=spec.entity, attribute_capabilities=tuple(_attribute(field) for field in spec.attributes)
                )
                for spec in sorted(list_entity_specs(), key=lambda spec: spec.entity)
            ),
            source_family_capabilities=tuple(sorted(sources, key=lambda value: value.name)),
            target_family_capabilities=tuple(sorted(targets, key=lambda value: value.name)),
            exporter_capabilities=tuple(sorted(exporters, key=lambda value: value.name)),
            source_suffix_capabilities=tuple(
                SourceSuffixCapability(
                    name=suffix,
                    consumers=tuple(
                        SourceConsumerCapability(element=fact.element, source_type=fact.source_type)
                        for fact in source_facts
                        if any(value.value == suffix for value in fact.file_formats)
                    ),
                )
                for suffix in suffixes
            ),
            source_distributions=tuple(
                SourceDistributionCapability(name=item.value, requires_full_pool=item.loads_all)
                for item in sorted(source_distributions, key=lambda item: item.value)
            ),
            numeric_distributions=tuple(
                NumericDistributionCapability(name=item.value, single_process_only=item in POSITIONAL_NUMBER_SEQUENCES)
                for item in sorted(numeric_distributions, key=lambda item: item.value)
            ),
        )

    def _project(self, name: str) -> ProjectStarter:
        document, acceptance = _example(name)
        return ProjectStarter(entry_xml=self._codec.compile(document).xml, acceptance=acceptance)

    def reference(self, request: ReferenceRequest) -> ReferenceResult:
        match request.topic:
            case ReferenceTopic.OVERVIEW:
                return ReferenceResult(
                    topic=request.topic,
                    content=(
                        "Author DM JSON, compile to XML, and declare expectations in each Build. "
                        "Codec support, parser validity, bounded evidence and external delivery are separate claims."
                    ),
                    next_topics=tuple(topic for topic in ReferenceTopic if topic != ReferenceTopic.OVERVIEW),
                )
            case ReferenceTopic.RULES:
                rules = tuple(
                    rule
                    for rule in (*authoring_rule_catalog(), *_xml_rule_catalog())
                    if request.name is None or str(rule.rule_id) == request.name
                )
                return ReferenceResult(
                    topic=request.topic,
                    name=request.name,
                    content="Build and CE XML rules with required repairs." if rules else "No matching rule.",
                    rules=rules,
                )
            case ReferenceTopic.EXPECTATIONS:
                schema = TypeAdapter(ExpectationIntent).json_schema()
                mapping = schema["discriminator"]["mapping"]
                expectation_entries = tuple(
                    AuthoringVariantReference(name=name, json_schema={"$ref": reference, "$defs": schema["$defs"]})
                    for name, reference in sorted(mapping.items())
                    if request.name is None or request.name == name
                )
                return ReferenceResult(
                    topic=request.topic,
                    name=request.name,
                    content="Expectations are transaction-scoped and are not recovered from persisted XML."
                    if expectation_entries
                    else "No matching expectation.",
                    entries=expectation_entries,
                )
            case ReferenceTopic.EXAMPLES:
                names = ("starter", "memstore")
                if request.name is None:
                    entries = tuple(AuthoringExampleReference(name=name, title=name) for name in names)
                elif request.name in names:
                    entries = (
                        AuthoringExampleReference(
                            name=request.name, title=request.name, project=self._project(request.name)
                        ),
                    )
                else:
                    entries = ()
                return ReferenceResult(
                    topic=request.topic,
                    name=request.name,
                    content=(
                        "Native CE examples; request one by name to compile it. "
                        "Compilation does not execute or verify its expectations."
                    )
                    if entries
                    else "No matching example.",
                    entries=entries,
                )
            case ReferenceTopic.ASSEMBLY:
                if request.name not in (None, "starter"):
                    return ReferenceResult(
                        topic=request.topic, name=request.name, content="No matching assembly.", entries=()
                    )
                return ReferenceResult(
                    topic=request.topic,
                    content=(
                        "Write the entry as datamimic.xml and every required expectation in acceptance/build.json, "
                        "then Build the project directory."
                    ),
                    entries=(
                        AuthoringAssemblyReference(
                            name="starter",
                            instruction="Write these two files, Build the project and inspect its typed readiness "
                            "and evidence.",
                            starter=self._project("starter"),
                        ),
                    ),
                )
            case ReferenceTopic.LEARNING:
                resources = (
                    AuthoringLearningReference(
                        name="migration",
                        path="docs/migrations/authoring-errors.md",
                        description="DM JSON, persisted XML, expectations, and CE verification guarantees.",
                    ),
                    AuthoringLearningReference(
                        name="context",
                        path="datamimic_ce/engine/runtime/contexts/geniter_context.py",
                        description=(
                            "Scripts use Python. Current-scope fields can resolve bare; this.field explicitly reads "
                            "the current record, parent.field its immediate parent, "
                            "and root.field the outermost record. "
                            "An existing outermost bare name wins a collision; qualify intermediate ancestor fields. "
                            "Variable records use dot access (row.field), the documented form; mapping access "
                            "(row['field'], dict(row)) also works. Nested rows need row.to_dict() for json.dumps. "
                            "__name__ interpolation belongs to string "
                            "and pattern attributes, not scripts."
                        ),
                    ),
                    AuthoringLearningReference(
                        name="timeseries",
                        path="datamimic_ce/engine/dsl/model/generation/timeseries.py",
                        description=(
                            "A generate window requires ISO start, end and interval together; end must follow start. "
                            "Count is the number of series (default 1). "
                            "Ticks per series are floor((end-start)/interval). "
                            "ts.now is the tick datetime, ts.step its zero-based index within the series, "
                            "and ts.series "
                            "the zero-based series index. Series run consecutively. "
                            "These clock values are deterministic; "
                            "other random fields still need rng_seed for replay. Avoid naming a field or variable ts."
                        ),
                    ),
                )
                learning_entries = tuple(
                    entry for entry in resources if request.name is None or entry.name == request.name
                )
                return ReferenceResult(
                    topic=request.topic,
                    name=request.name,
                    content="CE migration, script scope and time-series guidance."
                    if learning_entries
                    else "No matching learning resource.",
                    entries=learning_entries,
                )
        raise ValueError(f"unsupported reference topic: {request.topic}")


def _attribute(field: FieldSpec) -> AttributeCapability:
    return AttributeCapability(
        name=field.name,
        data_type=field.data_type,
        description=field.description,
        children=tuple(_attribute(child) for child in field.children),
    )


def _example(name: str) -> tuple[DmJsonDocumentV1, BuildRequestV5]:
    producer = DmJsonNodeV1(
        kind="generate",
        properties={"name": "rows", "count": "2"},
        children=(DmJsonNodeV1(kind="key", properties={"name": "id", "generator": "IncrementGenerator"}),),
    )
    children: tuple[DmJsonNodeV1, ...] = (producer,)
    expectations: tuple[ExactCountExpectation, ...] = (
        ExactCountExpectation(subject=ProductRowsSubject(product="rows"), count=2),
    )
    roles: tuple[ProductRoleDeclaration, ...] = ()
    if name == "memstore":
        roles = (
            ProductRoleDeclaration(product="rows", field="id", role=IdentifierRole()),
            ProductRoleDeclaration(
                product="readback", field="id", role=ForeignKeyRole(parent_product="rows", parent_field="id")
            ),
        )
        producer = producer.model_copy(update={"properties": {**producer.properties, "target": "store"}})
        children = (
            DmJsonNodeV1(kind="memstore", properties={"id": "store"}),
            producer,
            DmJsonNodeV1(
                kind="generate",
                properties={"name": "readback", "source": "store", "source_entity": "rows", "traversal_count": 2},
                children=(DmJsonNodeV1(kind="key", properties={"name": "id", "script": "this.id"}),),
            ),
        )
        expectations += (ExactCountExpectation(subject=ProductRowsSubject(product="readback"), count=2),)
    return (
        DmJsonDocumentV1(root=DmJsonNodeV1(kind="setup", properties={"rng_seed": 7}, children=children)),
        BuildRequestV5(expectations=expectations, product_roles=roles, max_count=10, sample_rows=5),
    )


def _xml_rule_catalog() -> tuple[RuleCatalogEntry, ...]:
    from datamimic_ce.authoring.domain.rule_catalog import RuleSeverity, authoring_rule_definition
    from datamimic_ce.authoring.domain.rules import ALL_RULES

    definitions = (*[rule.definition for rule in ALL_RULES], authoring_rule_definition("DM407"))
    return tuple(
        RuleCatalogEntry(
            rule_id=definition.id,
            category="xml" if definition.id != "DM407" else "delivery",
            severity="error"
            if definition.severity is RuleSeverity.ERROR
            else "warning"
            if definition.severity is RuleSeverity.WARNING
            else "info",
            description=definition.explanation,
            applicability="Raw XML lint." if definition.id != "DM407" else "Build delivery policy.",
            owner=RuleOwner.VALIDATION if definition.id != "DM407" else RuleOwner.SAFETY,
            remediation=definition.fix_hint,
            title=definition.title,
            provenance=definition.provenance,
            valid_example=definition.valid_example,
            invalid_example=definition.invalid_example,
            advisory_severity=definition.advisory_severity.value if definition.advisory_severity else None,
            blocks_verification=definition.blocks_verification,
        )
        for definition in sorted(definitions, key=lambda definition: definition.id)
    )
