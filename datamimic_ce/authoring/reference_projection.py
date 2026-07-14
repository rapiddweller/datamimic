# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Compact authoring references projected from canonical intent models."""

from collections.abc import Callable, Mapping
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter

from datamimic_ce.authoring.spec import (
    AllowedValuesExpectation,
    AuthoringSpecV1,
    ConstantField,
    DecimalRangeField,
    ExactCountExpectation,
    ExpectationIntentKind,
    FieldIntent,
    FieldIntentKind,
    FileExportTarget,
    ForeignKeyExpectation,
    ForeignKeyRole,
    GeneratedProduct,
    IdentifierRole,
    IncrementField,
    IntegerRangeField,
    MemstoreTarget,
    NestedGeneratedProduct,
    NestedListField,
    PatternField,
    PerParentCountExpectation,
    PersonEmailField,
    PersonNameField,
    ProductIntent,
    ProductIntentKind,
    RangeExpectation,
    RowConditionExpectation,
    ScriptField,
    StringLengthField,
    TargetIntentKind,
    UniqueExpectation,
    ValuesField,
    WeightedField,
)
from datamimic_ce.authoring.spec_examples import (
    minimal_product_example,
    minimal_source_product_example,
    minimal_time_series_product_example,
    product_example_kinds,
)


class AuthoringReferenceCategory(StrEnum):
    PRODUCT = "product"
    FIELD = "field"
    TARGET = "target"
    EXPECTATION = "expectation"
    EXAMPLE = "example"


class AuthoringExampleKind(StrEnum):
    FLAT = "flat"
    NESTED = "nested"
    SOURCE = "source"
    TIME_SERIES = "time_series"


class _Query(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProductReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.PRODUCT] = AuthoringReferenceCategory.PRODUCT
    kind: ProductIntentKind


class FieldReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.FIELD] = AuthoringReferenceCategory.FIELD
    kind: FieldIntentKind


class TargetReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.TARGET] = AuthoringReferenceCategory.TARGET
    kind: TargetIntentKind


class ExpectationReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.EXPECTATION] = AuthoringReferenceCategory.EXPECTATION
    kind: ExpectationIntentKind


class ExampleReferenceQuery(_Query):
    category: Literal[AuthoringReferenceCategory.EXAMPLE] = AuthoringReferenceCategory.EXAMPLE
    kind: AuthoringExampleKind


AuthoringReferenceQuery = Annotated[
    ProductReferenceQuery
    | FieldReferenceQuery
    | TargetReferenceQuery
    | ExpectationReferenceQuery
    | ExampleReferenceQuery,
    Field(discriminator="category"),
]
AUTHORING_REFERENCE_QUERY_ADAPTER: TypeAdapter[AuthoringReferenceQuery] = TypeAdapter(
    AuthoringReferenceQuery
)


class AuthoringReferenceProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    query: AuthoringReferenceQuery
    model: str
    required_fields: tuple[str, ...]
    allowed_fields: tuple[str, ...]
    fragment: dict[str, JsonValue]


ReferenceModel = (
    AuthoringSpecV1
    | ProductIntent
    | FieldIntent
    | FileExportTarget
    | MemstoreTarget
    | ExactCountExpectation
    | PerParentCountExpectation
    | UniqueExpectation
    | ForeignKeyExpectation
    | AllowedValuesExpectation
    | RangeExpectation
    | RowConditionExpectation
)
ReferenceFactory = Callable[[], ReferenceModel]


def _flat_example() -> AuthoringSpecV1:
    return AuthoringSpecV1(
        seed=42,
        products=(
            GeneratedProduct(
                name="customers",
                count=5,
                fields=(
                    IncrementField(name="customer_id", roles=(IdentifierRole(),)),
                    PersonNameField(name="name"),
                ),
                targets=(FileExportTarget(format="JSON"),),
            ),
        ),
        expectations=(ExactCountExpectation(product="customers", count=5),),
    )


def _nested_example() -> AuthoringSpecV1:
    return AuthoringSpecV1(
        seed=42,
        products=(
            GeneratedProduct(
                name="customers",
                count=4,
                fields=(IncrementField(name="customer_id", roles=(IdentifierRole(),)),),
                children=(
                    NestedGeneratedProduct(
                        name="orders",
                        count=2,
                        fields=(
                            IncrementField(name="order_no"),
                            ScriptField(
                                name="customer_id",
                                script="parent.customer_id",
                                roles=(
                                    ForeignKeyRole(
                                        parent_product="customers",
                                        parent_field="customer_id",
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        expectations=(
            PerParentCountExpectation(
                parent_product="customers",
                child_product="orders",
                count=2,
            ),
        ),
    )


def _source_example() -> AuthoringSpecV1:
    return AuthoringSpecV1(seed=42, products=(minimal_source_product_example(),))


def _time_series_example() -> AuthoringSpecV1:
    return AuthoringSpecV1(seed=42, products=(minimal_time_series_product_example(),))


_FIELD_FACTORIES: Mapping[FieldIntentKind, ReferenceFactory] = {
    FieldIntentKind.INCREMENT: lambda: IncrementField(name="id"),
    FieldIntentKind.PERSON_NAME: lambda: PersonNameField(name="name"),
    FieldIntentKind.PERSON_EMAIL: lambda: PersonEmailField(name="email"),
    FieldIntentKind.INTEGER_RANGE: lambda: IntegerRangeField(name="age", minimum=18, maximum=99),
    FieldIntentKind.DECIMAL_RANGE: lambda: DecimalRangeField(
        name="amount", minimum=Decimal("0.00"), maximum=Decimal("1000.00")
    ),
    FieldIntentKind.STRING_LENGTH: lambda: StringLengthField(name="code", minimum=4, maximum=12),
    FieldIntentKind.VALUES: lambda: ValuesField(name="status", values=("active", "inactive")),
    FieldIntentKind.WEIGHTED: lambda: WeightedField(
        name="tier", values=("standard", "premium"), weights=(8, 2)
    ),
    FieldIntentKind.PATTERN: lambda: PatternField(name="code", pattern="[A-Z]{2}[0-9]{4}"),
    FieldIntentKind.CONSTANT: lambda: ConstantField(name="country", value="DE"),
    FieldIntentKind.SCRIPT: lambda: ScriptField(name="label", script="this.name.upper()"),
    FieldIntentKind.NESTED_LIST: lambda: NestedListField(
        name="items",
        minimum_count=1,
        maximum_count=3,
        fields=(ValuesField(name="sku", values=("A", "B")),),
    ),
}
_TARGET_FACTORIES: Mapping[TargetIntentKind, ReferenceFactory] = {
    TargetIntentKind.FILE_EXPORT: lambda: FileExportTarget(format="JSON"),
    TargetIntentKind.MEMSTORE: lambda: MemstoreTarget(id="records_store"),
}
_EXPECTATION_FACTORIES: Mapping[ExpectationIntentKind, ReferenceFactory] = {
    ExpectationIntentKind.EXACT_COUNT: lambda: ExactCountExpectation(product="records", count=5),
    ExpectationIntentKind.PER_PARENT_COUNT: lambda: PerParentCountExpectation(
        parent_product="customers", child_product="orders", count=2
    ),
    ExpectationIntentKind.UNIQUE: lambda: UniqueExpectation(product="records", field="id"),
    ExpectationIntentKind.FOREIGN_KEY: lambda: ForeignKeyExpectation(
        child_product="orders",
        child_field="customer_id",
        parent_product="customers",
        parent_field="customer_id",
    ),
    ExpectationIntentKind.ALLOWED_VALUES: lambda: AllowedValuesExpectation(
        product="records", field="status", values=("active", "inactive")
    ),
    ExpectationIntentKind.RANGE: lambda: RangeExpectation(
        product="records",
        field="amount",
        minimum=Decimal("0.00"),
        maximum=Decimal("1000.00"),
    ),
    ExpectationIntentKind.ROW_CONDITION: lambda: RowConditionExpectation(
        product="records", condition="this.amount >= 0"
    ),
}
_EXAMPLE_FACTORIES: Mapping[AuthoringExampleKind, ReferenceFactory] = {
    AuthoringExampleKind.FLAT: _flat_example,
    AuthoringExampleKind.NESTED: _nested_example,
    AuthoringExampleKind.SOURCE: _source_example,
    AuthoringExampleKind.TIME_SERIES: _time_series_example,
}


def _model_for_query(query: AuthoringReferenceQuery) -> ReferenceModel:
    if isinstance(query, ProductReferenceQuery):
        return minimal_product_example(query.kind)
    if isinstance(query, FieldReferenceQuery):
        return _FIELD_FACTORIES[query.kind]()
    if isinstance(query, TargetReferenceQuery):
        return _TARGET_FACTORIES[query.kind]()
    if isinstance(query, ExpectationReferenceQuery):
        return _EXPECTATION_FACTORIES[query.kind]()
    return _EXAMPLE_FACTORIES[query.kind]()


def authoring_reference_projection(query: AuthoringReferenceQuery) -> AuthoringReferenceProjection:
    model = _model_for_query(query)
    model_type = type(model)
    fields = model_type.model_fields
    return AuthoringReferenceProjection(
        query=query,
        model=model_type.__name__,
        required_fields=tuple(name for name, field in fields.items() if field.is_required()),
        allowed_fields=tuple(fields),
        fragment=model.model_dump(mode="json", exclude_none=True),
    )


def reference_fragment_is_valid(query: AuthoringReferenceQuery) -> bool:
    model = _model_for_query(query)
    type(model).model_validate(authoring_reference_projection(query).fragment)
    return True


def list_authoring_reference_queries() -> tuple[AuthoringReferenceQuery, ...]:
    return (
        *(ProductReferenceQuery(kind=kind) for kind in ProductIntentKind),
        *(FieldReferenceQuery(kind=kind) for kind in FieldIntentKind),
        *(TargetReferenceQuery(kind=kind) for kind in TargetIntentKind),
        *(ExpectationReferenceQuery(kind=kind) for kind in ExpectationIntentKind),
        *(ExampleReferenceQuery(kind=kind) for kind in AuthoringExampleKind),
    )


def projection_catalog_is_exhaustive() -> bool:
    """Fail closed if any canonical kind lacks exactly one compact projection."""

    product_models = [minimal_product_example(kind) for kind in ProductIntentKind]
    field_models = [_FIELD_FACTORIES[kind]() for kind in FieldIntentKind]
    target_models = [_TARGET_FACTORIES[kind]() for kind in TargetIntentKind]
    expectation_models = [_EXPECTATION_FACTORIES[kind]() for kind in ExpectationIntentKind]
    return (
        set(_FIELD_FACTORIES) == set(FieldIntentKind)
        and set(_TARGET_FACTORIES) == set(TargetIntentKind)
        and set(_EXPECTATION_FACTORIES) == set(ExpectationIntentKind)
        and product_example_kinds() == frozenset(ProductIntentKind)
        and len({type(model) for model in product_models}) == len(tuple(ProductIntentKind))
        and len({type(model) for model in field_models}) == len(tuple(FieldIntentKind))
        and len({type(model) for model in target_models}) == len(tuple(TargetIntentKind))
        and len({type(model) for model in expectation_models}) == len(tuple(ExpectationIntentKind))
        and all(
            model.model_dump(mode="json")["kind"] == kind
            for model, kind in zip(product_models, ProductIntentKind, strict=True)
        )
        and all(
            model.model_dump(mode="json")["kind"] == kind
            for model, kind in zip(field_models, FieldIntentKind, strict=True)
        )
        and all(
            model.model_dump(mode="json")["kind"] == kind
            for model, kind in zip(target_models, TargetIntentKind, strict=True)
        )
        and all(
            model.model_dump(mode="json")["kind"] == kind
            for model, kind in zip(expectation_models, ExpectationIntentKind, strict=True)
        )
    )


__all__ = [
    "AUTHORING_REFERENCE_QUERY_ADAPTER",
    "AuthoringExampleKind",
    "AuthoringReferenceCategory",
    "AuthoringReferenceProjection",
    "AuthoringReferenceQuery",
    "ExampleReferenceQuery",
    "ExpectationReferenceQuery",
    "FieldReferenceQuery",
    "ProductReferenceQuery",
    "TargetReferenceQuery",
    "authoring_reference_projection",
    "list_authoring_reference_queries",
    "projection_catalog_is_exhaustive",
    "reference_fragment_is_valid",
]
