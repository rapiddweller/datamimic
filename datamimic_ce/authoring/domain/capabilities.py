# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Runtime-free catalog values; declarations are not execution evidence."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, assert_never

from pydantic import Field, JsonValue, model_validator

from datamimic_ce.engine.dsl.vocabulary.contracts.dsl_element import BoundedExecutionProfile, ElementContentMode

from .common import AuthoringModel, NonEmptyStrictStr


class CapabilityDomain(StrEnum):
    ELEMENT = "element"
    GENERATOR = "generator"
    CONVERTER = "converter"
    ENTITY = "entity"
    SOURCE_FAMILY = "source_family"
    TARGET_FAMILY = "target_family"
    EXPORTER = "exporter"
    SOURCE_SUFFIX = "source_suffix"
    SOURCE_DISTRIBUTION = "source_distribution"
    NUMERIC_DISTRIBUTION = "numeric_distribution"


class AttributeCapability(AuthoringModel):
    name: NonEmptyStrictStr
    data_type: str
    description: str = ""
    children: tuple[AttributeCapability, ...] = ()


class ElementPropertyCapability(AuthoringModel):
    name: NonEmptyStrictStr
    xml_name: NonEmptyStrictStr
    required: bool
    description: str = ""


class AuthoringElementCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.ELEMENT] = CapabilityDomain.ELEMENT
    name: NonEmptyStrictStr
    aliases: tuple[str, ...] = ()
    attributes: tuple[ElementPropertyCapability, ...] = ()
    children: tuple[str, ...] | None = ()
    singleton_children: tuple[str, ...] = ()
    content_modes: tuple[ElementContentMode, ...] = ()
    bounded_execution: BoundedExecutionProfile
    properties_schema: dict[str, JsonValue]


class GeneratorCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.GENERATOR] = CapabilityDomain.GENERATOR
    name: NonEmptyStrictStr
    parameters: tuple[str, ...]


class ConverterCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.CONVERTER] = CapabilityDomain.CONVERTER
    name: NonEmptyStrictStr


class EntityCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.ENTITY] = CapabilityDomain.ENTITY
    name: NonEmptyStrictStr
    attribute_capabilities: tuple[AttributeCapability, ...]


class SourceConsumerCapability(AuthoringModel):
    element: str
    source_type: str | None = None
    suffixes: tuple[str, ...] = ()


class SourceFamilyCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.SOURCE_FAMILY] = CapabilityDomain.SOURCE_FAMILY
    name: NonEmptyStrictStr
    requires_client: bool
    consumers: tuple[SourceConsumerCapability, ...]


class TargetFamilyCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.TARGET_FAMILY] = CapabilityDomain.TARGET_FAMILY
    name: NonEmptyStrictStr
    requires_client: bool
    operations: tuple[str, ...]


class ExporterTargetCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.EXPORTER] = CapabilityDomain.EXPORTER
    name: NonEmptyStrictStr
    output_kind: Literal["file", "diagnostic"]


class SourceSuffixCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.SOURCE_SUFFIX] = CapabilityDomain.SOURCE_SUFFIX
    name: NonEmptyStrictStr
    consumers: tuple[SourceConsumerCapability, ...]


class SourceDistributionCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.SOURCE_DISTRIBUTION] = CapabilityDomain.SOURCE_DISTRIBUTION
    name: NonEmptyStrictStr
    requires_full_pool: bool


class NumericDistributionCapability(AuthoringModel):
    domain: Literal[CapabilityDomain.NUMERIC_DISTRIBUTION] = CapabilityDomain.NUMERIC_DISTRIBUTION
    name: NonEmptyStrictStr
    single_process_only: bool


CatalogCapability = Annotated[
    AuthoringElementCapability
    | GeneratorCapability
    | ConverterCapability
    | EntityCapability
    | SourceFamilyCapability
    | TargetFamilyCapability
    | ExporterTargetCapability
    | SourceSuffixCapability
    | SourceDistributionCapability
    | NumericDistributionCapability,
    Field(discriminator="domain"),
]


class CapabilityFound(AuthoringModel):
    ok: Literal[True] = True
    domain: CapabilityDomain
    name: NonEmptyStrictStr
    capability: CatalogCapability

    @model_validator(mode="after")
    def identity_matches(self) -> CapabilityFound:
        if self.domain != self.capability.domain or self.name != self.capability.name:
            raise ValueError("capability identity must match its lookup")
        return self


class CapabilityNotFound(AuthoringModel):
    ok: Literal[False] = False
    domain: CapabilityDomain
    name: NonEmptyStrictStr
    error: Literal["capability_not_found"] = "capability_not_found"
    available_names: tuple[str, ...]


CapabilityLookupResult = Annotated[CapabilityFound | CapabilityNotFound, Field(discriminator="ok")]


class DslCatalogSnapshot(AuthoringModel):
    element_capabilities: tuple[AuthoringElementCapability, ...] = ()
    generator_capabilities: tuple[GeneratorCapability, ...] = ()
    converter_capabilities: tuple[ConverterCapability, ...] = ()
    entities: tuple[EntityCapability, ...] = ()
    source_family_capabilities: tuple[SourceFamilyCapability, ...] = ()
    target_family_capabilities: tuple[TargetFamilyCapability, ...] = ()
    exporter_capabilities: tuple[ExporterTargetCapability, ...] = ()
    source_suffix_capabilities: tuple[SourceSuffixCapability, ...] = ()
    source_distributions: tuple[SourceDistributionCapability, ...] = ()
    numeric_distributions: tuple[NumericDistributionCapability, ...] = ()

    def _values(self, domain: CapabilityDomain) -> tuple[CatalogCapability, ...]:
        match domain:
            case CapabilityDomain.ELEMENT:
                return self.element_capabilities
            case CapabilityDomain.GENERATOR:
                return self.generator_capabilities
            case CapabilityDomain.CONVERTER:
                return self.converter_capabilities
            case CapabilityDomain.ENTITY:
                return self.entities
            case CapabilityDomain.SOURCE_FAMILY:
                return self.source_family_capabilities
            case CapabilityDomain.TARGET_FAMILY:
                return self.target_family_capabilities
            case CapabilityDomain.EXPORTER:
                return self.exporter_capabilities
            case CapabilityDomain.SOURCE_SUFFIX:
                return self.source_suffix_capabilities
            case CapabilityDomain.SOURCE_DISTRIBUTION:
                return self.source_distributions
            case CapabilityDomain.NUMERIC_DISTRIBUTION:
                return self.numeric_distributions
        assert_never(domain)

    def capability_names(self, domain: CapabilityDomain) -> tuple[str, ...]:
        return tuple(value.name for value in self._values(domain))

    def capability(self, domain: CapabilityDomain, name: str) -> CapabilityLookupResult:
        for value in self._values(domain):
            if value.name == name:
                return CapabilityFound(domain=domain, name=name, capability=value)
        return CapabilityNotFound(domain=domain, name=name, available_names=self.capability_names(domain))

    def to_dict(self) -> dict[str, object]:
        return self.model_dump(mode="json")

    def to_index_dict(self) -> dict[str, object]:
        return {domain.value: list(self.capability_names(domain)) for domain in CapabilityDomain}
