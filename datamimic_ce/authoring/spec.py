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

from collections.abc import Mapping
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, InvalidOperation, localcontext
from math import isfinite
from typing import Annotated, Final, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    ValidationError,
    model_validator,
)
from pydantic.json_schema import JsonDict, JsonValue
from pydantic_core import InitErrorDetails, PydanticCustomError

from datamimic_ce._compat import StrEnum, assert_never
from datamimic_ce.constants.element_constants import EL_DATABASE, EL_GENERATE, EL_MONGODB
from datamimic_ce.exporters.exporter_util import buffered_exporter_names
from datamimic_ce.model.constraints import is_source_file

PositiveStrictInt = Annotated[StrictInt, Field(gt=0)]
NonNegativeStrictInt = Annotated[StrictInt, Field(ge=0)]
NonEmptyStrictStr = Annotated[StrictStr, Field(min_length=1)]
INTENT_REPAIR_ALIASES_SCHEMA_KEY = "x-datamimic-repair-aliases"
_ORDERED_BOUNDS_ERROR = "minimum must not exceed maximum"
_DECIMAL_FLOAT_ROUNDTRIP_ERROR = "range is not representable by runtime FloatGenerator"
MAX_DECIMAL_SCALE: Final[int] = 15


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


class ProductIntentKind(StrEnum):
    """Canonical discriminator vocabulary for authoring products."""

    GENERATED = "generated"
    SOURCE = "source"
    TIME_SERIES = "time_series"


class SourceIntentKind(StrEnum):
    """Canonical discriminator vocabulary for authoring sources."""

    FILE = "file"
    MEMSTORE = "memstore"


class TargetIntentKind(StrEnum):
    """Canonical discriminator vocabulary for authoring targets."""

    FILE_EXPORT = "file_export"
    MEMSTORE = "memstore"


class ExpectationIntentKind(StrEnum):
    """Canonical discriminator vocabulary for explicit acceptance intent."""

    EXACT_COUNT = "exact_count"
    PER_PARENT_COUNT = "per_parent_count"
    UNIQUE = "unique"
    FOREIGN_KEY = "foreign_key"
    ALLOWED_VALUES = "allowed_values"
    RANGE = "range"
    ROW_CONDITION = "row_condition"


class FieldRoleKind(StrEnum):
    """Canonical discriminator vocabulary for semantic field roles."""

    IDENTIFIER = "identifier"
    FOREIGN_KEY = "foreign_key"
    TIMESTAMP = "timestamp"
    VALUE = "value"


class IntentModelValidationIssueType(StrEnum):
    """Stable custom validation signals owned by the Intent Model."""

    UNKNOWN_PRODUCT_REFERENCE = "unknown_product_reference"
    UNSUPPORTED_NESTED_PRODUCT_CHILDREN = "unsupported_nested_product_children"
    UNSUPPORTED_DATABASE_PRODUCT = "unsupported_database_product"


class IntentModelPathSegment(StrEnum):
    """Canonical field names used in model-owned validation locations."""

    PRODUCTS = "products"
    EXPECTATIONS = "expectations"
    CHILDREN = "children"
    FIELDS = "fields"
    SOURCE = "source"
    TARGETS = "targets"


INTENT_MODEL_VALIDATION_MESSAGES: dict[IntentModelValidationIssueType, str] = {
    IntentModelValidationIssueType.UNSUPPORTED_NESTED_PRODUCT_CHILDREN: (
        "Nested product relationships cannot define child products in AuthoringSpecV1"
    ),
    IntentModelValidationIssueType.UNSUPPORTED_DATABASE_PRODUCT: (
        "Database and MongoDB sources/targets are not supported by AuthoringSpecV1; the engine supports them "
        "through raw XML <database>/<mongodb> clients (lint -> dry-run -> run)"
    ),
}

# Engine client elements that authoring V1 does not model: a known capability, not a typo
_UNSUPPORTED_CLIENT_KINDS = frozenset({EL_DATABASE, EL_MONGODB})


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
ProductKind = Literal[
    ProductIntentKind.GENERATED,
    ProductIntentKind.SOURCE,
    ProductIntentKind.TIME_SERIES,
]


class IntentModel(BaseModel):
    """Strict base contract shared by all authoring-intent variants."""

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class IdentifierRole(IntentModel):
    kind: Literal[FieldRoleKind.IDENTIFIER] = FieldRoleKind.IDENTIFIER


class ForeignKeyRole(IntentModel):
    kind: Literal[FieldRoleKind.FOREIGN_KEY] = FieldRoleKind.FOREIGN_KEY
    parent_product: str = Field(min_length=1)
    parent_field: str = Field(min_length=1)


class TimestampRole(IntentModel):
    kind: Literal[FieldRoleKind.TIMESTAMP] = FieldRoleKind.TIMESTAMP


class ValueRole(IntentModel):
    kind: Literal[FieldRoleKind.VALUE] = FieldRoleKind.VALUE


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
            raise ValueError(_ORDERED_BOUNDS_ERROR)
        return self


class DecimalRangeField(FieldIntent):
    kind: Literal[FieldIntentKind.DECIMAL_RANGE] = FieldIntentKind.DECIMAL_RANGE
    minimum: Decimal
    maximum: Decimal
    scale: NonNegativeStrictInt | None = Field(
        default=None,
        le=MAX_DECIMAL_SCALE,
        description="Supported scale is 0 through 15 decimal places; runtime range generation uses FloatGenerator.",
    )

    @model_validator(mode="after")
    def _ordered_bounds(self) -> DecimalRangeField:
        if self.minimum > self.maximum:
            raise ValueError(_ORDERED_BOUNDS_ERROR)
        try:
            minimum, maximum = self.runtime_bounds()
        except (InvalidOperation, OverflowError, ValueError) as error:
            raise ValueError(_DECIMAL_FLOAT_ROUNDTRIP_ERROR) from error
        if minimum > maximum:
            raise ValueError("range contains no value at the requested scale")
        if self.scale is not None:
            quantum = Decimal(1).scaleb(-self.scale)
            try:
                runtime_minimum_float = float(minimum)
                runtime_maximum_float = float(maximum)
                runtime_quantum_float = float(quantum)
                runtime_minimum = Decimal(str(runtime_minimum_float))
                runtime_maximum = Decimal(str(runtime_maximum_float))
                runtime_quantum = Decimal(str(runtime_quantum_float))
            except (InvalidOperation, OverflowError, ValueError) as error:
                raise ValueError(_DECIMAL_FLOAT_ROUNDTRIP_ERROR) from error
            if (
                not isfinite(runtime_minimum_float)
                or not isfinite(runtime_maximum_float)
                or not isfinite(runtime_quantum_float)
                or not isfinite(runtime_maximum_float - runtime_minimum_float)
                or runtime_quantum != quantum
                or runtime_minimum > runtime_maximum
                or runtime_minimum < self.minimum
                or runtime_maximum > self.maximum
            ):
                raise ValueError(_DECIMAL_FLOAT_ROUNDTRIP_ERROR)
        return self

    def runtime_bounds(self) -> tuple[Decimal, Decimal]:
        if self.scale is None:
            return self.minimum, self.maximum
        quantum = Decimal(1).scaleb(-self.scale)
        precision = max(
            len(self.minimum.as_tuple().digits),
            len(self.maximum.as_tuple().digits),
            self.minimum.adjusted() + self.scale + 1,
            self.maximum.adjusted() + self.scale + 1,
        )
        with localcontext() as context:
            context.prec = precision
            return (
                self.minimum.quantize(quantum, rounding=ROUND_CEILING),
                self.maximum.quantize(quantum, rounding=ROUND_FLOOR),
            )


class StringLengthField(FieldIntent):
    kind: Literal[FieldIntentKind.STRING_LENGTH] = FieldIntentKind.STRING_LENGTH
    minimum: NonNegativeStrictInt
    maximum: NonNegativeStrictInt

    @model_validator(mode="after")
    def _ordered_bounds(self) -> StringLengthField:
        if self.minimum > self.maximum:
            raise ValueError(_ORDERED_BOUNDS_ERROR)
        return self


class ValuesField(FieldIntent):
    kind: Literal[FieldIntentKind.VALUES] = FieldIntentKind.VALUES
    values: tuple[str, ...] = Field(
        min_length=1,
        description="The business-domain values emitted by this field.",
    )


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
    kind: Literal[SourceIntentKind.FILE] = SourceIntentKind.FILE
    path: RuntimeFileSourcePath
    separator: str | None = None
    distribution: Literal["ordered"] = "ordered"


class MemstoreSource(IntentModel):
    kind: Literal[SourceIntentKind.MEMSTORE] = SourceIntentKind.MEMSTORE
    id: RuntimeMemstoreSourceId
    product: str | None = Field(
        default=None,
        min_length=1,
        json_schema_extra={INTENT_REPAIR_ALIASES_SCHEMA_KEY: ["type"]},
    )
    distribution: Literal["ordered"] = "ordered"


SourceIntent = Annotated[FileSource | MemstoreSource, Field(discriminator="kind")]


def _file_export_schema(schema: JsonDict) -> None:
    properties = schema.get("properties")
    if isinstance(properties, dict):
        format_schema = properties.get("format")
        if isinstance(format_schema, dict):
            enum_values: list[JsonValue] = []
            enum_values.extend(sorted(buffered_exporter_names()))
            format_schema["enum"] = enum_values


class FileExportTarget(IntentModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        json_schema_extra=_file_export_schema,
    )

    kind: Literal[TargetIntentKind.FILE_EXPORT] = TargetIntentKind.FILE_EXPORT
    format: RegisteredFileExporterName
    export_uri: str | None = Field(default=None, min_length=1)


class MemstoreTarget(IntentModel):
    kind: Literal[TargetIntentKind.MEMSTORE] = TargetIntentKind.MEMSTORE
    id: str = Field(min_length=1)


TargetIntent = Annotated[FileExportTarget | MemstoreTarget, Field(discriminator="kind")]


class NestedRelationship(IntentModel):
    """Declares that a child product is generated inside each parent record."""

    kind: Literal["nested"] = "nested"


class ProductIntent(IntentModel):
    name: str = Field(min_length=1)
    fields: tuple[FieldIntentUnion, ...] = ()
    targets: tuple[TargetIntent, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _reject_database_clients(cls, value: object) -> object:
        if not isinstance(value, Mapping):
            return value
        targets = value.get(IntentModelPathSegment.TARGETS)
        source = value.get(IntentModelPathSegment.SOURCE)
        locations: list[tuple[tuple[str | int, ...], object]] = []
        if isinstance(targets, list):
            locations += [
                ((IntentModelPathSegment.TARGETS, index, "kind"), target.get("kind"))
                for index, target in enumerate(targets)
                if isinstance(target, Mapping)
            ]
        if isinstance(source, Mapping):
            locations.append(((IntentModelPathSegment.SOURCE, "kind"), source.get("kind")))
        issue_type = IntentModelValidationIssueType.UNSUPPORTED_DATABASE_PRODUCT
        errors = [
            InitErrorDetails(
                type=PydanticCustomError(issue_type, INTENT_MODEL_VALIDATION_MESSAGES[issue_type]),
                loc=loc,
                input=kind,
            )
            for loc, kind in locations
            if kind in _UNSUPPORTED_CLIENT_KINDS
        ]
        if errors:
            raise ValidationError.from_exception_data(cls.__name__, errors)
        return value

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
    kind: Literal[ProductIntentKind.GENERATED] = ProductIntentKind.GENERATED
    count: PositiveStrictInt
    relationship: NestedRelationship = Field(default_factory=NestedRelationship)

    @model_validator(mode="before")
    @classmethod
    def _reject_child_products(cls, value: object) -> object:
        children = IntentModelPathSegment.CHILDREN
        if not isinstance(value, Mapping) or children not in value:
            return value
        issue_type = IntentModelValidationIssueType.UNSUPPORTED_NESTED_PRODUCT_CHILDREN
        raise ValidationError.from_exception_data(
            cls.__name__,
            [
                InitErrorDetails(
                    type=PydanticCustomError(
                        issue_type,
                        INTENT_MODEL_VALIDATION_MESSAGES[issue_type],
                    ),
                    loc=(children,),
                    input=value[children],
                )
            ],
        )

    @model_validator(mode="after")
    def _has_fields(self) -> NestedGeneratedProduct:
        if not self.fields:
            raise ValueError("nested generated product needs fields")
        return self


class GeneratedProduct(ProductIntent):
    kind: Literal[ProductIntentKind.GENERATED] = ProductIntentKind.GENERATED
    count: PositiveStrictInt
    children: tuple[NestedGeneratedProduct, ...] = ()

    @model_validator(mode="after")
    def _has_output_shape(self) -> GeneratedProduct:
        if not self.fields and not self.children:
            raise ValueError("generated product needs fields or child products")
        return self


class SourceProduct(ProductIntent):
    kind: Literal[ProductIntentKind.SOURCE] = ProductIntentKind.SOURCE
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
    kind: Literal[ProductIntentKind.TIME_SERIES] = ProductIntentKind.TIME_SERIES
    series_count: PositiveStrictInt = Field(
        default=1,
        description=(
            "Number of parallel temporal series. It multiplies rows in the window and does not create an "
            "implicit data field, dimension, or value domain. Model each business dimension named in the intent "
            "as its own field and place that dimension's values on the same field."
        ),
    )
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
    kind: Literal[ExpectationIntentKind.EXACT_COUNT] = ExpectationIntentKind.EXACT_COUNT
    product: str = Field(min_length=1)
    list_field: str | None = Field(default=None, min_length=1)
    count: NonNegativeStrictInt = Field(
        json_schema_extra={INTENT_REPAIR_ALIASES_SCHEMA_KEY: ["exact_count"]},
    )


class PerParentCountExpectation(IntentModel):
    kind: Literal[ExpectationIntentKind.PER_PARENT_COUNT] = ExpectationIntentKind.PER_PARENT_COUNT
    parent_product: str = Field(min_length=1)
    child_product: str = Field(min_length=1)
    count: NonNegativeStrictInt


class UniqueExpectation(IntentModel):
    kind: Literal[ExpectationIntentKind.UNIQUE] = ExpectationIntentKind.UNIQUE
    product: str = Field(min_length=1)
    list_field: str | None = Field(default=None, min_length=1)
    field: str = Field(min_length=1)
    scope: Literal["global", "per_parent"] = "global"


class ForeignKeyExpectation(IntentModel):
    kind: Literal[ExpectationIntentKind.FOREIGN_KEY] = ExpectationIntentKind.FOREIGN_KEY
    child_product: str = Field(min_length=1)
    child_field: str = Field(min_length=1)
    parent_product: str = Field(min_length=1)
    parent_field: str = Field(min_length=1)


class AllowedValuesExpectation(IntentModel):
    kind: Literal[ExpectationIntentKind.ALLOWED_VALUES] = ExpectationIntentKind.ALLOWED_VALUES
    product: str = Field(min_length=1)
    list_field: str | None = Field(default=None, min_length=1)
    field: str = Field(min_length=1)
    values: tuple[str, ...] = Field(
        min_length=1,
        description="The expected business-domain values for the named field.",
    )


class RangeExpectation(IntentModel):
    kind: Literal[ExpectationIntentKind.RANGE] = ExpectationIntentKind.RANGE
    product: str = Field(min_length=1)
    list_field: str | None = Field(default=None, min_length=1)
    field: str = Field(min_length=1)
    minimum: Decimal
    maximum: Decimal

    @model_validator(mode="after")
    def _ordered_bounds(self) -> RangeExpectation:
        if self.minimum > self.maximum:
            raise ValueError(_ORDERED_BOUNDS_ERROR)
        return self


class RowConditionExpectation(IntentModel):
    kind: Literal[ExpectationIntentKind.ROW_CONDITION] = ExpectationIntentKind.ROW_CONDITION
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


class _IntentGraphIndex:
    def __init__(self, products: tuple[ProductIntentUnion, ...]) -> None:
        self.products = _intent_products(products)
        self.fields = _intent_fields(self.products)
        self.nested_fields = _intent_nested_fields(self.products)
        self.nested_edges = _intent_nested_edges(products)

    def require_product(self, name: str, context: str) -> None:
        if name not in self.products:
            raise ValueError(f"{context} references unknown product '{name}'")

    def require_field(self, product: str, field: str, context: str) -> None:
        self.require_product(product, context)
        if field not in self.fields[product]:
            raise ValueError(f"{context} references unknown field '{field}' on product '{product}'")

    def require_nested_list(self, product: str, list_field: str, context: str) -> None:
        self.require_product(product, context)
        if list_field not in self.nested_fields[product]:
            raise ValueError(f"{context} references unknown nested_list field '{product}.{list_field}'")

    def require_nested_inner_field(self, product: str, list_field: str, field: str, context: str) -> None:
        self.require_nested_list(product, list_field, context)
        if field not in {item.name for item in self.nested_fields[product][list_field].fields}:
            raise ValueError(
                f"{context} references unknown field '{field}' in nested_list '{product}.{list_field}'"
            )


def _intent_products(
    products: tuple[ProductIntentUnion, ...],
) -> dict[str, ProductIntent | NestedGeneratedProduct]:
    names: list[str] = []
    products_by_name: dict[str, ProductIntent | NestedGeneratedProduct] = {}
    for product in products:
        names.append(product.name)
        products_by_name[product.name] = product
        if isinstance(product, GeneratedProduct):
            names.extend(child.name for child in product.children)
            products_by_name.update({child.name: child for child in product.children})
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"product names must be unique: {', '.join(duplicates)}")
    return products_by_name


def _intent_fields(
    products: dict[str, ProductIntent | NestedGeneratedProduct],
) -> dict[str, set[str]]:
    return {name: {field.name for field in product.fields} for name, product in products.items()}


def _intent_nested_fields(
    products: dict[str, ProductIntent | NestedGeneratedProduct],
) -> dict[str, dict[str, NestedListField]]:
    return {
        name: {field.name: field for field in product.fields if isinstance(field, NestedListField)}
        for name, product in products.items()
    }


def _intent_nested_edges(
    products: tuple[ProductIntentUnion, ...],
) -> set[tuple[str, str]]:
    return {
        (product.name, child.name)
        for product in products
        if isinstance(product, GeneratedProduct)
        for child in product.children
    }


def _validate_intent_roles(index: _IntentGraphIndex) -> None:
    for product_name, product in index.products.items():
        for field in product.fields:
            _validate_nested_identifier_role(product_name, product, field)
            for role in field.roles:
                if isinstance(role, ForeignKeyRole):
                    index.require_field(
                        role.parent_product,
                        role.parent_field,
                        f"foreign-key role on {product_name}.{field.name}",
                    )


def _validate_nested_identifier_role(
    product_name: str,
    product: ProductIntent | NestedGeneratedProduct,
    field: FieldIntentUnion,
) -> None:
    if not isinstance(product, NestedGeneratedProduct):
        return
    if not isinstance(field, IncrementField):
        return
    if any(isinstance(role, IdentifierRole) for role in field.roles):
        raise ValueError(
            f"nested Increment field '{product_name}.{field.name}' is local per "
            "parent and cannot claim the global identifier role"
        )


def _validate_unique_expectations(expectations: tuple[ExpectationIntent, ...]) -> None:
    duplicate_kinds = [
        expectation.kind for index, expectation in enumerate(expectations) if expectation in expectations[:index]
    ]
    if duplicate_kinds:
        kinds = ", ".join(duplicate_kinds)
        raise ValueError(f"explicit expectations must be unique; duplicates: {kinds}")


def _expectation_product_references(expectation: ExpectationIntent) -> tuple[tuple[str, str], ...]:
    if isinstance(expectation, ExactCountExpectation | RowConditionExpectation):
        return (("product", expectation.product),)
    if isinstance(expectation, PerParentCountExpectation):
        return (
            ("parent_product", expectation.parent_product),
            ("child_product", expectation.child_product),
        )
    if isinstance(expectation, UniqueExpectation | AllowedValuesExpectation | RangeExpectation):
        return (("product", expectation.product),)
    if isinstance(expectation, ForeignKeyExpectation):
        return (
            ("child_product", expectation.child_product),
            ("parent_product", expectation.parent_product),
        )
    assert_never(expectation)


def _unknown_product_errors(
    expectations: tuple[ExpectationIntent, ...],
    index: _IntentGraphIndex,
    path_prefix: tuple[str, ...],
) -> list[InitErrorDetails]:
    known = ", ".join(sorted(index.products))
    known_products = tuple(sorted(index.products))
    errors: list[InitErrorDetails] = []
    for position, expectation in enumerate(expectations):
        for field, product in _expectation_product_references(expectation):
            if product in index.products:
                continue
            message = (
                f"{expectation.kind} expectation references unknown product '{product}'. "
                f"Known products: {known}"
            )
            errors.append(
                InitErrorDetails(
                    type=PydanticCustomError(
                        IntentModelValidationIssueType.UNKNOWN_PRODUCT_REFERENCE,
                        message,
                        {"known_products": known_products},
                    ),
                    loc=(*path_prefix, position, field),
                    input=product,
                )
            )
    return errors


def _validate_expectation(
    expectation: ExpectationIntent,
    index: _IntentGraphIndex,
) -> None:
    context = f"{expectation.kind} expectation"
    if isinstance(expectation, ExactCountExpectation | RowConditionExpectation):
        index.require_product(expectation.product, context)
        if isinstance(expectation, ExactCountExpectation) and expectation.list_field is not None:
            index.require_nested_list(expectation.product, expectation.list_field, context)
    elif isinstance(expectation, PerParentCountExpectation):
        index.require_product(expectation.parent_product, context)
        index.require_product(expectation.child_product, context)
        if (expectation.parent_product, expectation.child_product) not in index.nested_edges:
            raise ValueError(
                f"{context} requires a nested parent-child relationship between "
                f"'{expectation.parent_product}' and '{expectation.child_product}'"
            )
    elif isinstance(expectation, UniqueExpectation | AllowedValuesExpectation | RangeExpectation):
        if expectation.list_field is None:
            index.require_field(expectation.product, expectation.field, context)
        else:
            index.require_nested_inner_field(
                expectation.product,
                expectation.list_field,
                expectation.field,
                context,
            )
    else:
        index.require_field(expectation.child_product, expectation.child_field, context)
        index.require_field(expectation.parent_product, expectation.parent_field, context)


def _expectation_error_field(
    expectation: ExpectationIntent,
    index: _IntentGraphIndex,
) -> str:
    if isinstance(expectation, ExactCountExpectation):
        return "list_field" if expectation.list_field is not None else "product"
    if isinstance(expectation, UniqueExpectation | AllowedValuesExpectation | RangeExpectation):
        if expectation.list_field is None:
            return "field"
        nested_fields = index.nested_fields.get(expectation.product, {})
        return "list_field" if expectation.list_field not in nested_fields else "field"
    if isinstance(expectation, PerParentCountExpectation):
        return "child_product"
    if isinstance(expectation, ForeignKeyExpectation):
        child_fields = index.fields.get(expectation.child_product, set())
        return "child_field" if expectation.child_field not in child_fields else "parent_field"
    return "product"


def _validate_expectation_references(
    expectations: tuple[ExpectationIntent, ...],
    index: _IntentGraphIndex,
    path_prefix: tuple[str, ...],
    title: str,
) -> None:
    errors = _unknown_product_errors(expectations, index, path_prefix)
    if not errors:
        for position, expectation in enumerate(expectations):
            try:
                _validate_expectation(expectation, index)
            except ValueError as error:
                errors.append(
                    InitErrorDetails(
                        type=PydanticCustomError("value_error", str(error)),
                        loc=(*path_prefix, position, _expectation_error_field(expectation, index)),
                        input=expectation,
                    )
                )
    if errors:
        raise ValidationError.from_exception_data(title, errors)


def _validate_expectations(
    expectations: tuple[ExpectationIntent, ...],
    index: _IntentGraphIndex,
) -> None:
    _validate_unique_expectations(expectations)
    _validate_expectation_references(
        expectations,
        index,
        (IntentModelPathSegment.EXPECTATIONS,),
        AuthoringSpecV1.__name__,
    )


def validate_expectation_products(
    expectations: tuple[ExpectationIntent, ...],
    products: tuple[ProductIntentUnion, ...],
    path_prefix: tuple[str, ...],
) -> None:
    """Reject expectation references before runtime capture can make them unevaluable."""

    _validate_expectation_references(
        expectations,
        _IntentGraphIndex(products),
        path_prefix,
        "ExpectationProducts",
    )


class AuthoringSpecV1(IntentModel):
    """Canonical contents of a ``model.dm.json`` authoring artifact."""

    version: Literal["1"] = "1"
    products: tuple[ProductIntentUnion, ...] = Field(min_length=1)
    seed: StrictInt | None = None
    expectations: tuple[ExpectationIntent, ...] = ()

    @model_validator(mode="after")
    def _unique_product_names(self) -> AuthoringSpecV1:
        index = _IntentGraphIndex(self.products)
        _validate_intent_roles(index)
        _validate_expectations(self.expectations, index)
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
    "ExpectationIntentKind",
    "FieldKind",
    "FieldIntentKind",
    "FieldIntentUnion",
    "FieldRoleKind",
    "INTENT_MODEL_VALIDATION_MESSAGES",
    "INTENT_REPAIR_ALIASES_SCHEMA_KEY",
    "IntentModelPathSegment",
    "IntentModelValidationIssueType",
    "LeafFieldKind",
    "NonEmptyStrictStr",
    "NonNegativeStrictInt",
    "PositiveStrictInt",
    "ProductKind",
    "ProductIntentKind",
    "ProductIntentUnion",
    "RegisteredFileExporterName",
    "RuntimeFileSourcePath",
    "RuntimeMemstoreSourceId",
    "SPEC_JSON_SCHEMA",
    "SPEC_PROMPT_GUIDE",
    "SourceIntentKind",
    "TargetIntentKind",
    "authoring_spec_json_schema",
    "validate_expectation_products",
]
