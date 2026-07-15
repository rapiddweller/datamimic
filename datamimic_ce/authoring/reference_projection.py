# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Typed authoring discovery projected from the canonical intent models."""

from collections.abc import Mapping
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

from datamimic_ce.authoring.spec import (
    AllowedValuesExpectation,
    ConstantField,
    DecimalRangeField,
    ExactCountExpectation,
    ExpectationIntentKind,
    FieldIntentKind,
    FileExportTarget,
    FileSource,
    ForeignKeyExpectation,
    GeneratedProduct,
    IncrementField,
    IntegerRangeField,
    MemstoreSource,
    MemstoreTarget,
    NestedListField,
    PatternField,
    PerParentCountExpectation,
    PersonEmailField,
    PersonNameField,
    ProductIntentKind,
    RangeExpectation,
    RowConditionExpectation,
    ScriptField,
    SourceIntentKind,
    SourceProduct,
    StringLengthField,
    TargetIntentKind,
    TimeSeriesProduct,
    UniqueExpectation,
    ValuesField,
    WeightedField,
)


class AuthoringReferenceCategory(StrEnum):
    """Canonical discriminated-union families exposed for discovery."""

    PRODUCT = "product"
    SOURCE = "source"
    FIELD = "field"
    TARGET = "target"
    EXPECTATION = "expectation"


class _Query(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProductReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.PRODUCT] = AuthoringReferenceCategory.PRODUCT
    kind: ProductIntentKind


class FieldReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.FIELD] = AuthoringReferenceCategory.FIELD
    kind: FieldIntentKind


class SourceReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.SOURCE] = AuthoringReferenceCategory.SOURCE
    kind: SourceIntentKind


class TargetReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.TARGET] = AuthoringReferenceCategory.TARGET
    kind: TargetIntentKind


class ExpectationReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.EXPECTATION] = AuthoringReferenceCategory.EXPECTATION
    kind: ExpectationIntentKind


AuthoringReferenceQuery = Annotated[
    ProductReferenceQuery
    | SourceReferenceQuery
    | FieldReferenceQuery
    | TargetReferenceQuery
    | ExpectationReferenceQuery,
    Field(discriminator="category"),
]
AUTHORING_REFERENCE_QUERY_ADAPTER: TypeAdapter[AuthoringReferenceQuery] = TypeAdapter(
    AuthoringReferenceQuery
)


class AuthoringReferenceProjection(BaseModel):
    """Schema-only description of one canonical intent variant."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    query: AuthoringReferenceQuery
    model: str
    required_fields: tuple[str, ...]
    allowed_fields: tuple[str, ...]
    json_schema: dict[str, JsonValue]


IntentModelType = type[BaseModel]
_JSON_SCHEMA_ADAPTER: TypeAdapter[dict[str, JsonValue]] = TypeAdapter(
    dict[str, JsonValue]
)

_PRODUCT_MODELS: Mapping[ProductIntentKind, IntentModelType] = {
    ProductIntentKind.GENERATED: GeneratedProduct,
    ProductIntentKind.SOURCE: SourceProduct,
    ProductIntentKind.TIME_SERIES: TimeSeriesProduct,
}
_SOURCE_MODELS: Mapping[SourceIntentKind, IntentModelType] = {
    SourceIntentKind.FILE: FileSource,
    SourceIntentKind.MEMSTORE: MemstoreSource,
}
_FIELD_MODELS: Mapping[FieldIntentKind, IntentModelType] = {
    FieldIntentKind.INCREMENT: IncrementField,
    FieldIntentKind.PERSON_NAME: PersonNameField,
    FieldIntentKind.PERSON_EMAIL: PersonEmailField,
    FieldIntentKind.INTEGER_RANGE: IntegerRangeField,
    FieldIntentKind.DECIMAL_RANGE: DecimalRangeField,
    FieldIntentKind.STRING_LENGTH: StringLengthField,
    FieldIntentKind.VALUES: ValuesField,
    FieldIntentKind.WEIGHTED: WeightedField,
    FieldIntentKind.PATTERN: PatternField,
    FieldIntentKind.CONSTANT: ConstantField,
    FieldIntentKind.SCRIPT: ScriptField,
    FieldIntentKind.NESTED_LIST: NestedListField,
}
_TARGET_MODELS: Mapping[TargetIntentKind, IntentModelType] = {
    TargetIntentKind.FILE_EXPORT: FileExportTarget,
    TargetIntentKind.MEMSTORE: MemstoreTarget,
}
_EXPECTATION_MODELS: Mapping[ExpectationIntentKind, IntentModelType] = {
    ExpectationIntentKind.EXACT_COUNT: ExactCountExpectation,
    ExpectationIntentKind.PER_PARENT_COUNT: PerParentCountExpectation,
    ExpectationIntentKind.UNIQUE: UniqueExpectation,
    ExpectationIntentKind.FOREIGN_KEY: ForeignKeyExpectation,
    ExpectationIntentKind.ALLOWED_VALUES: AllowedValuesExpectation,
    ExpectationIntentKind.RANGE: RangeExpectation,
    ExpectationIntentKind.ROW_CONDITION: RowConditionExpectation,
}


def _model_type(query: AuthoringReferenceQuery) -> IntentModelType:
    if isinstance(query, ProductReferenceQuery):
        return _PRODUCT_MODELS[query.kind]
    if isinstance(query, SourceReferenceQuery):
        return _SOURCE_MODELS[query.kind]
    if isinstance(query, FieldReferenceQuery):
        return _FIELD_MODELS[query.kind]
    if isinstance(query, TargetReferenceQuery):
        return _TARGET_MODELS[query.kind]
    return _EXPECTATION_MODELS[query.kind]


def authoring_reference_projection(
    query: AuthoringReferenceQuery,
) -> AuthoringReferenceProjection:
    """Project one query without constructing a sample intent instance."""

    model_type = _model_type(query)
    fields = model_type.model_fields
    return AuthoringReferenceProjection(
        query=query,
        model=model_type.__name__,
        required_fields=tuple(
            name for name, field in fields.items() if field.is_required()
        ),
        allowed_fields=tuple(fields),
        json_schema=_JSON_SCHEMA_ADAPTER.validate_python(
            model_type.model_json_schema()
        ),
    )


def list_authoring_reference_queries() -> tuple[AuthoringReferenceQuery, ...]:
    """Enumerate every canonical discriminated-union variant."""

    return (
        *(ProductReferenceQuery(kind=kind) for kind in ProductIntentKind),
        *(SourceReferenceQuery(kind=kind) for kind in SourceIntentKind),
        *(FieldReferenceQuery(kind=kind) for kind in FieldIntentKind),
        *(TargetReferenceQuery(kind=kind) for kind in TargetIntentKind),
        *(ExpectationReferenceQuery(kind=kind) for kind in ExpectationIntentKind),
    )


def projection_catalog_is_exhaustive() -> bool:
    """Return whether every canonical variant has exactly one model owner."""

    mappings: tuple[tuple[set[StrEnum], set[StrEnum]], ...] = (
        (set(_PRODUCT_MODELS), set(ProductIntentKind)),
        (set(_SOURCE_MODELS), set(SourceIntentKind)),
        (set(_FIELD_MODELS), set(FieldIntentKind)),
        (set(_TARGET_MODELS), set(TargetIntentKind)),
        (set(_EXPECTATION_MODELS), set(ExpectationIntentKind)),
    )
    model_types = (
        *_PRODUCT_MODELS.values(),
        *_SOURCE_MODELS.values(),
        *_FIELD_MODELS.values(),
        *_TARGET_MODELS.values(),
        *_EXPECTATION_MODELS.values(),
    )
    return (
        all(actual == expected for actual, expected in mappings)
        and len(set(model_types)) == len(model_types)
    )


__all__ = [
    "AUTHORING_REFERENCE_QUERY_ADAPTER",
    "AuthoringReferenceCategory",
    "AuthoringReferenceProjection",
    "AuthoringReferenceQuery",
    "ExpectationReferenceQuery",
    "FieldReferenceQuery",
    "ProductReferenceQuery",
    "SourceReferenceQuery",
    "TargetReferenceQuery",
    "authoring_reference_projection",
    "list_authoring_reference_queries",
    "projection_catalog_is_exhaustive",
]
