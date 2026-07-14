# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Versioned business-intent model for DATAMIMIC authoring.

The models in this module describe what an author wants to produce.  They do
not mirror XML element models; translating this intent into executable DSL is
the compiler's responsibility.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    model_validator,
)
from pydantic.json_schema import JsonDict, JsonValue

from datamimic_ce.constants.element_constants import EL_GENERATE
from datamimic_ce.exporters.exporter_util import buffered_exporter_names
from datamimic_ce.model.constraints import is_source_file

PositiveStrictInt = Annotated[StrictInt, Field(gt=0)]
NonNegativeStrictInt = Annotated[StrictInt, Field(ge=0)]
NonEmptyStrictStr = Annotated[StrictStr, Field(min_length=1)]


class FieldIntentKind(StrEnum):
    """Canonical discriminator vocabulary for authoring field intent."""

    INCREMENT = "increment"
    PERSON_NAME = "person_name"
    PERSON_EMAIL = "person_email"
    INTEGER_RANGE = "int_range"
    DECIMAL_RANGE = "decimal_range"
    STRING_LENGTH = "string_length"
    VALUES = "values"
    WEIGHTED = "weighted"
    PATTERN = "pattern"
    CONSTANT = "constant"
    SCRIPT = "script"
    NESTED_LIST = "nested_list"


LeafFieldKind = Literal[
    FieldIntentKind.INCREMENT,
    FieldIntentKind.PERSON_NAME,
    FieldIntentKind.PERSON_EMAIL,
    FieldIntentKind.INTEGER_RANGE,
    FieldIntentKind.DECIMAL_RANGE,
    FieldIntentKind.STRING_LENGTH,
    FieldIntentKind.VALUES,
    FieldIntentKind.WEIGHTED,
    FieldIntentKind.PATTERN,
    FieldIntentKind.CONSTANT,
    FieldIntentKind.SCRIPT,
]
FieldKind = Literal[LeafFieldKind, FieldIntentKind.NESTED_LIST]
ProductKind = Literal["generated", "source", "time_series"]


class IntentModel(BaseModel):
    """Strict base contract shared by all authoring-intent variants."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class IdentifierRole(IntentModel):
    kind: Literal["identifier"] = "identifier"


class ForeignKeyRole(IntentModel):
    kind: Literal["foreign_key"] = "foreign_key"
    parent_product: str = Field(min_length=1)
    parent_field: str = Field(min_length=1)


class TimestampRole(IntentModel):
    kind: Literal["timestamp"] = "timestamp"


class ValueRole(IntentModel):
    kind: Literal["value"] = "value"


FieldRole = Annotated[
    IdentifierRole | ForeignKeyRole | TimestampRole | ValueRole,
    Field(discriminator="kind"),
]


class FieldIntent(IntentModel):
    """Business metadata common to all field-generation strategies."""

    name: str = Field(min_length=1)
    roles: tuple[FieldRole, ...] = ()


class IncrementField(FieldIntent):
    kind: Literal[FieldIntentKind.INCREMENT] = FieldIntentKind.INCREMENT


class PersonNameField(FieldIntent):
    kind: Literal[FieldIntentKind.PERSON_NAME] = FieldIntentKind.PERSON_NAME


class PersonEmailField(FieldIntent):
    kind: Literal[FieldIntentKind.PERSON_EMAIL] = FieldIntentKind.PERSON_EMAIL


class IntegerRangeField(FieldIntent):
    kind: Literal[FieldIntentKind.INTEGER_RANGE] = FieldIntentKind.INTEGER_RANGE
    minimum: StrictInt
    maximum: StrictInt
    unique: StrictBool = False

    @model_validator(mode="after")
    def _ordered_bounds(self) -> IntegerRangeField:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class DecimalRangeField(FieldIntent):
    kind: Literal[FieldIntentKind.DECIMAL_RANGE] = FieldIntentKind.DECIMAL_RANGE
    minimum: Decimal
    maximum: Decimal

    @model_validator(mode="after")
    def _ordered_bounds(self) -> DecimalRangeField:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class StringLengthField(FieldIntent):
    kind: Literal[FieldIntentKind.STRING_LENGTH] = FieldIntentKind.STRING_LENGTH
    minimum: NonNegativeStrictInt
    maximum: NonNegativeStrictInt

    @model_validator(mode="after")
    def _ordered_bounds(self) -> StringLengthField:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class ValuesField(FieldIntent):
    kind: Literal[FieldIntentKind.VALUES] = FieldIntentKind.VALUES
    values: tuple[str, ...] = Field(min_length=1)


class WeightedField(FieldIntent):
    kind: Literal[FieldIntentKind.WEIGHTED] = FieldIntentKind.WEIGHTED
    values: tuple[str, ...] = Field(min_length=1)
    weights: tuple[StrictFloat | StrictInt, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _matching_weights(self) -> WeightedField:
        if len(self.values) != len(self.weights):
            raise ValueError("values and weights must have the same length")
        if any(weight < 0 for weight in self.weights):
            raise ValueError("weights must not be negative")
        if not any(self.weights):
            raise ValueError("at least one weight must be positive")
        return self


class PatternField(FieldIntent):
    kind: Literal[FieldIntentKind.PATTERN] = FieldIntentKind.PATTERN
    pattern: str = Field(min_length=1)


class ConstantField(FieldIntent):
    kind: Literal[FieldIntentKind.CONSTANT] = FieldIntentKind.CONSTANT
    value: str


class ScriptField(FieldIntent):
    kind: Literal[FieldIntentKind.SCRIPT] = FieldIntentKind.SCRIPT
    script: str = Field(min_length=1)


LeafFieldIntent = Annotated[
    IncrementField
    | PersonNameField
    | PersonEmailField
    | IntegerRangeField
    | DecimalRangeField
    | StringLengthField
    | ValuesField
    | WeightedField
    | PatternField
    | ConstantField
    | ScriptField,
    Field(discriminator="kind"),
]


class NestedListField(FieldIntent):
    kind: Literal[FieldIntentKind.NESTED_LIST] = FieldIntentKind.NESTED_LIST
    minimum_count: NonNegativeStrictInt
    maximum_count: NonNegativeStrictInt
    fields: tuple[LeafFieldIntent, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _ordered_counts(self) -> NestedListField:
        if self.minimum_count > self.maximum_count:
            raise ValueError("minimum_count must not exceed maximum_count")
        if any(isinstance(field, IntegerRangeField) and field.unique for field in self.fields):
            raise ValueError("unique integer ranges are unsupported inside nested_list")
        names = [field.name for field in self.fields]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"nested_list field names must be unique: {', '.join(duplicates)}")
        return self


FieldIntentUnion = Annotated[LeafFieldIntent | NestedListField, Field(discriminator="kind")]


def _validate_runtime_file_source(value: str) -> str:
    if not is_source_file(value, EL_GENERATE):
        raise ValueError("path does not use a runtime-supported source-file suffix")
    return value


def _validate_runtime_memstore_source(value: str) -> str:
    if is_source_file(value, EL_GENERATE):
        raise ValueError("memstore id would be dispatched as a file source; use kind='file'")
    return value


def _validate_registered_file_exporter(value: str) -> str:
    if value not in buffered_exporter_names():
        expected = ", ".join(sorted(buffered_exporter_names()))
        raise ValueError(f"unsupported file exporter '{value}'; expected: {expected}")
    return value


RuntimeFileSourcePath = Annotated[
    StrictStr,
    Field(min_length=1),
    AfterValidator(_validate_runtime_file_source),
]
RuntimeMemstoreSourceId = Annotated[
    StrictStr,
    Field(min_length=1),
    AfterValidator(_validate_runtime_memstore_source),
]
RegisteredFileExporterName = Annotated[
    StrictStr,
    Field(min_length=1),
    AfterValidator(_validate_registered_file_exporter),
]


class FileSource(IntentModel):
    kind: Literal["file"] = "file"
    path: RuntimeFileSourcePath
    separator: str | None = None
    distribution: Literal["ordered"] = "ordered"


class MemstoreSource(IntentModel):
    kind: Literal["memstore"] = "memstore"
    id: RuntimeMemstoreSourceId
    product: str | None = Field(default=None, min_length=1)
    distribution: Literal["ordered"] = "ordered"


SourceIntent = Annotated[FileSource | MemstoreSource, Field(discriminator="kind")]


def _file_export_schema(schema: JsonDict) -> None:
    properties = schema.get("properties")
    if isinstance(properties, dict):
        format_schema = properties.get("format")
        if isinstance(format_schema, dict):
            enum_values: list[JsonValue] = [
                name for name in sorted(buffered_exporter_names())
            ]
            format_schema["enum"] = enum_values


class FileExportTarget(IntentModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        json_schema_extra=_file_export_schema,
    )

    kind: Literal["file_export"] = "file_export"
    format: RegisteredFileExporterName
    export_uri: str | None = Field(default=None, min_length=1)


class MemstoreTarget(IntentModel):
    kind: Literal["memstore"] = "memstore"
    id: str = Field(min_length=1)


TargetIntent = Annotated[FileExportTarget | MemstoreTarget, Field(discriminator="kind")]


class NestedRelationship(IntentModel):
    """Declares that a child product is generated inside each parent record."""

    kind: Literal["nested"] = "nested"


class ProductIntent(IntentModel):
    name: str = Field(min_length=1)
    fields: tuple[FieldIntentUnion, ...] = ()
    targets: tuple[TargetIntent, ...] = ()

    @model_validator(mode="after")
    def _target_export_uri_is_unambiguous(self) -> ProductIntent:
        field_names = [field.name for field in self.fields]
        duplicate_fields = sorted({name for name in field_names if field_names.count(name) > 1})
        if duplicate_fields:
            raise ValueError(f"field names must be unique: {', '.join(duplicate_fields)}")

        target_keys = [
            (target.kind, target.format if isinstance(target, FileExportTarget) else target.id)
            for target in self.targets
        ]
        duplicate_targets = sorted({key for key in target_keys if target_keys.count(key) > 1})
        if duplicate_targets:
            rendered = ", ".join(f"{kind}:{name}" for kind, name in duplicate_targets)
            raise ValueError(f"targets must be unique: {rendered}")

        export_uris = {
            target.export_uri
            for target in self.targets
            if isinstance(target, FileExportTarget) and target.export_uri is not None
        }
        if len(export_uris) > 1:
            raise ValueError("all file-export targets of one product must share one export_uri")
        return self


class NestedGeneratedProduct(ProductIntent):
    kind: Literal["generated"] = "generated"
    count: PositiveStrictInt
    relationship: NestedRelationship = Field(default_factory=NestedRelationship)

    @model_validator(mode="after")
    def _has_fields(self) -> NestedGeneratedProduct:
        if not self.fields:
            raise ValueError("nested generated product needs fields")
        return self


class GeneratedProduct(ProductIntent):
    kind: Literal["generated"] = "generated"
    count: PositiveStrictInt
    children: tuple[NestedGeneratedProduct, ...] = ()

    @model_validator(mode="after")
    def _has_output_shape(self) -> GeneratedProduct:
        if not self.fields and not self.children:
            raise ValueError("generated product needs fields or child products")
        return self


class SourceProduct(ProductIntent):
    kind: Literal["source"] = "source"
    source: SourceIntent

    @model_validator(mode="after")
    def _has_fields(self) -> SourceProduct:
        if not self.fields:
            raise ValueError("source product needs fields")
        return self


class TimeSeriesWindow(IntentModel):
    start: str = Field(min_length=1)
    end: str = Field(min_length=1)
    interval: str = Field(min_length=1)


class TimeSeriesProduct(ProductIntent):
    kind: Literal["time_series"] = "time_series"
    series_count: PositiveStrictInt = 1
    window: TimeSeriesWindow

    @model_validator(mode="after")
    def _has_fields(self) -> TimeSeriesProduct:
        if not self.fields:
            raise ValueError("time-series product needs fields")
        return self


ProductIntentUnion = Annotated[
    GeneratedProduct | SourceProduct | TimeSeriesProduct,
    Field(discriminator="kind"),
]


class ExactCountExpectation(IntentModel):
    kind: Literal["exact_count"] = "exact_count"
    product: str = Field(min_length=1)
    count: NonNegativeStrictInt


class PerParentCountExpectation(IntentModel):
    kind: Literal["per_parent_count"] = "per_parent_count"
    parent_product: str = Field(min_length=1)
    child_product: str = Field(min_length=1)
    count: NonNegativeStrictInt


class UniqueExpectation(IntentModel):
    kind: Literal["unique"] = "unique"
    product: str = Field(min_length=1)
    field: str = Field(min_length=1)
    scope: Literal["global", "per_parent"] = "global"


class ForeignKeyExpectation(IntentModel):
    kind: Literal["foreign_key"] = "foreign_key"
    child_product: str = Field(min_length=1)
    child_field: str = Field(min_length=1)
    parent_product: str = Field(min_length=1)
    parent_field: str = Field(min_length=1)


class AllowedValuesExpectation(IntentModel):
    kind: Literal["allowed_values"] = "allowed_values"
    product: str = Field(min_length=1)
    field: str = Field(min_length=1)
    values: tuple[str, ...] = Field(min_length=1)


class RangeExpectation(IntentModel):
    kind: Literal["range"] = "range"
    product: str = Field(min_length=1)
    field: str = Field(min_length=1)
    minimum: Decimal
    maximum: Decimal

    @model_validator(mode="after")
    def _ordered_bounds(self) -> RangeExpectation:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class RowConditionExpectation(IntentModel):
    kind: Literal["row_condition"] = "row_condition"
    product: str = Field(min_length=1)
    condition: str = Field(min_length=1)
    result_type: Literal["bool"] = "bool"


ExpectationIntent = Annotated[
    ExactCountExpectation
    | PerParentCountExpectation
    | UniqueExpectation
    | ForeignKeyExpectation
    | AllowedValuesExpectation
    | RangeExpectation
    | RowConditionExpectation,
    Field(discriminator="kind"),
]


class AuthoringSpecV1(IntentModel):
    """Canonical contents of a ``model.dm.json`` authoring artifact."""

    version: Literal["1"] = "1"
    products: tuple[ProductIntentUnion, ...] = Field(min_length=1)
    seed: StrictInt | None = None
    expectations: tuple[ExpectationIntent, ...] = ()

    @model_validator(mode="after")
    def _unique_product_names(self) -> AuthoringSpecV1:
        names: list[str] = []
        products_by_name: dict[str, ProductIntent | NestedGeneratedProduct] = {}
        for product in self.products:
            names.append(product.name)
            products_by_name[product.name] = product
            if isinstance(product, GeneratedProduct):
                names.extend(child.name for child in product.children)
                products_by_name.update({child.name: child for child in product.children})
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"product names must be unique: {', '.join(duplicates)}")

        fields_by_product = {
            name: {field.name for field in product.fields} for name, product in products_by_name.items()
        }

        def require_product(name: str, context: str) -> None:
            if name not in products_by_name:
                raise ValueError(f"{context} references unknown product '{name}'")

        def require_field(product: str, field: str, context: str) -> None:
            require_product(product, context)
            if field not in fields_by_product[product]:
                raise ValueError(f"{context} references unknown field '{field}' on product '{product}'")

        for product_name, resolved_product in products_by_name.items():
            for field in resolved_product.fields:
                if (
                    isinstance(resolved_product, NestedGeneratedProduct)
                    and isinstance(field, IncrementField)
                    and any(isinstance(role, IdentifierRole) for role in field.roles)
                ):
                    raise ValueError(
                        f"nested Increment field '{product_name}.{field.name}' is local per "
                        "parent and cannot claim the global identifier role"
                    )
                for role in field.roles:
                    if isinstance(role, ForeignKeyRole):
                        require_field(
                            role.parent_product,
                            role.parent_field,
                            f"foreign-key role on {product_name}.{field.name}",
                        )

        nested_edges = {
            (product.name, child.name)
            for product in self.products
            if isinstance(product, GeneratedProduct)
            for child in product.children
        }
        duplicate_expectation_kinds = [
            expectation.kind
            for index, expectation in enumerate(self.expectations)
            if expectation in self.expectations[:index]
        ]
        if duplicate_expectation_kinds:
            kinds = ", ".join(duplicate_expectation_kinds)
            raise ValueError(f"explicit expectations must be unique; duplicates: {kinds}")
        for expectation in self.expectations:
            context = f"{expectation.kind} expectation"
            if isinstance(expectation, ExactCountExpectation | RowConditionExpectation):
                require_product(expectation.product, context)
            elif isinstance(expectation, PerParentCountExpectation):
                require_product(expectation.parent_product, context)
                require_product(expectation.child_product, context)
                if (expectation.parent_product, expectation.child_product) not in nested_edges:
                    raise ValueError(
                        f"{context} requires a nested parent-child relationship between "
                        f"'{expectation.parent_product}' and '{expectation.child_product}'"
                    )
            elif isinstance(
                expectation,
                UniqueExpectation | AllowedValuesExpectation | RangeExpectation,
            ):
                require_field(expectation.product, expectation.field, context)
            elif isinstance(expectation, ForeignKeyExpectation):
                require_field(
                    expectation.child_product,
                    expectation.child_field,
                    context,
                )
                require_field(
                    expectation.parent_product,
                    expectation.parent_field,
                    context,
                )
        return self


SPEC_PROMPT_GUIDE = """Produce one canonical model.dm.json document with version \"1\".
Choose each product's explicit kind: generated, source, or time_series. Choose every
field/source/target/expectation by its explicit kind discriminator; do not invent Python
helpers to express supported intent. A generated product may contain one level of
generated children. Database and MongoDB products are not supported by authoring V1."""


def authoring_spec_json_schema() -> dict[str, object]:
    """Project the structured-output schema directly from the Intent SPOT."""

    return AuthoringSpecV1.model_json_schema()


SPEC_JSON_SCHEMA = authoring_spec_json_schema()


__all__ = [
    "AuthoringSpecV1",
    "ExpectationIntent",
    "FieldKind",
    "FieldIntentKind",
    "FieldIntentUnion",
    "LeafFieldKind",
    "NonEmptyStrictStr",
    "NonNegativeStrictInt",
    "PositiveStrictInt",
    "ProductKind",
    "ProductIntentUnion",
    "RegisteredFileExporterName",
    "RuntimeFileSourcePath",
    "RuntimeMemstoreSourceId",
    "SPEC_JSON_SCHEMA",
    "SPEC_PROMPT_GUIDE",
    "authoring_spec_json_schema",
]
