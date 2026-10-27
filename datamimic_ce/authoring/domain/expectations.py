# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from __future__ import annotations

import json
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, ClassVar, Literal, get_args

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator
from pydantic.json_schema import JsonDict

from .common import AuthoringModel, NonEmptyStrictStr, NonNegativeStrictInt
from .row_conditions import ROW_CONDITION_GRAMMAR, parse_row_condition

INTENT_REPAIR_ALIASES_SCHEMA_KEY = "x-datamimic-repair-aliases"


def _publish_alias_choices(schema: JsonDict, model: type[BaseModel]) -> None:
    """Publish every AliasChoices spelling of a field, which pydantic leaves out of the schema: the same value
    schema, never beside the field name, and one of the names required."""
    properties, required = schema["properties"], schema["required"]
    if not isinstance(properties, dict) or not isinstance(required, list):
        raise TypeError("a model schema has properties and required")
    spelled: list[str] = []
    alternatives: list[JsonValue] = []
    excluded: JsonDict = {}
    for name in model.model_fields:
        alias = model.model_fields[name].validation_alias
        if not isinstance(alias, AliasChoices):
            continue
        spellings = [choice for choice in alias.choices if isinstance(choice, str) and choice != name]
        for spelling in spellings:
            properties[spelling] = properties[name]
            excluded[spelling] = {"not": {"required": [name]}}
        spelled.append(name)
        alternatives.append({"anyOf": [{"required": [choice]} for choice in (name, *spellings)]})
    schema["required"] = [name for name in required if name not in spelled]
    schema["dependentSchemas"] = excluded
    schema["allOf"] = alternatives


class ExpectationIntentKind(StrEnum):
    EXACT_COUNT = "exact_count"
    PER_PARENT_COUNT = "per_parent_count"
    UNIQUE = "unique"
    FOREIGN_KEY = "foreign_key"
    ALLOWED_VALUES = "allowed_values"
    RANGE = "range"
    FIXED_VALUE = "fixed_value"
    FIELD_PRESENT = "field_present"
    FIELD_ABSENT = "field_absent"
    ROW_CONDITION = "row_condition"


class ExpectationSubjectKind(StrEnum):
    PRODUCT = "product"
    PER_PARENT = "per_parent"
    DECLARED_SINK = "declared_sink"


class DeclaredSinkIdentity(AuthoringModel):
    kind: Literal["database", "mongodb"]
    environment: NonEmptyStrictStr
    entity: NonEmptyStrictStr


class ProductRowsSubject(AuthoringModel):
    """All captured rows owned by one Authoring product."""

    kind: Literal[ExpectationSubjectKind.PRODUCT] = Field(
        default=ExpectationSubjectKind.PRODUCT, description="Expectation subject identity; must be 'product'."
    )
    product: NonEmptyStrictStr = Field(description="Product whose complete captured row set is evaluated.")
    list_field: NonEmptyStrictStr | None = None


class PerParentRowsSubject(AuthoringModel):
    """Captured child rows partitioned by their immediate parent product row."""

    kind: Literal[ExpectationSubjectKind.PER_PARENT] = Field(
        default=ExpectationSubjectKind.PER_PARENT, description="Expectation subject identity; must be 'per_parent'."
    )
    parent_product: NonEmptyStrictStr = Field(description="Immediate parent product defining each partition.")
    child_product: NonEmptyStrictStr = Field(description="Nested child product evaluated inside every partition.")


class DeclaredSinkRowsSubject(AuthoringModel):
    """Union of captured rows routed to one declared Authoring sink identity."""

    kind: Literal[ExpectationSubjectKind.DECLARED_SINK] = Field(
        default=ExpectationSubjectKind.DECLARED_SINK,
        description="Expectation subject identity; must be 'declared_sink'.",
    )
    sink: DeclaredSinkIdentity = Field(
        description="Declared database or MongoDB insert destination; this does not prove external target state."
    )


ProductOrSinkSubject = Annotated[ProductRowsSubject | DeclaredSinkRowsSubject, Field(discriminator="kind")]
UniqueSubject = Annotated[
    ProductRowsSubject | PerParentRowsSubject | DeclaredSinkRowsSubject, Field(discriminator="kind")
]


class FieldSelection(AuthoringModel):
    """One field selected from a product or declared-sink row set."""

    subject: ProductOrSinkSubject = Field(description="Captured row set containing the selected field.")
    field: NonEmptyStrictStr = Field(description="Captured field selected from every contributing row.")


class ExactCountExpectation(AuthoringModel):
    """Require one product or declared sink to contain exactly the declared captured rows."""

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "exact_count",
        "subject": {"kind": "product", "product": "customers"},
        "count": 100,
    }

    kind: Literal[ExpectationIntentKind.EXACT_COUNT] = Field(
        default=ExpectationIntentKind.EXACT_COUNT, description="Expectation identity; must be 'exact_count'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink row set whose count is checked.")
    count: NonNegativeStrictInt = Field(
        description="Exact number of rows expected for the product.",
        json_schema_extra={INTENT_REPAIR_ALIASES_SCHEMA_KEY: ["exact_count"]},
    )


class PerParentCountExpectation(AuthoringModel):
    """Require each parent row to produce exactly the declared number of child rows."""

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "per_parent_count",
        "subject": {"kind": "per_parent", "parent_product": "orders", "child_product": "items"},
        "count": 3,
    }

    kind: Literal[ExpectationIntentKind.PER_PARENT_COUNT] = Field(
        default=ExpectationIntentKind.PER_PARENT_COUNT, description="Expectation identity; must be 'per_parent_count'."
    )
    subject: PerParentRowsSubject = Field(description="Nested child rows partitioned by immediate parent row.")
    count: NonNegativeStrictInt = Field(description="Exact child rows expected for each parent row.")


class UniqueExpectation(AuthoringModel):
    """Require captured field values to be unique within one explicit row-set subject."""

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "unique",
        "subject": {"kind": "product", "product": "orders"},
        "field": "external_order_id",
    }

    kind: Literal[ExpectationIntentKind.UNIQUE] = Field(
        default=ExpectationIntentKind.UNIQUE, description="Expectation identity; must be 'unique'."
    )
    subject: UniqueSubject = Field(description="Product, per-parent partition, or declared-sink union under test.")
    field: NonEmptyStrictStr = Field(
        description=(
            "Field whose captured values must be unique; declare external business keys explicitly "
            "rather than relying on singleton samples."
        )
    )

    scope: Literal["global", "per_parent"] = "global"


class ForeignKeyExpectation(AuthoringModel):
    """Require every captured child reference to exist in the parent product's key set."""

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "foreign_key",
        "child": {"subject": {"kind": "product", "product": "orders"}, "field": "customer_id"},
        "parent": {"subject": {"kind": "product", "product": "customers"}, "field": "id"},
    }

    kind: Literal[ExpectationIntentKind.FOREIGN_KEY] = Field(
        default=ExpectationIntentKind.FOREIGN_KEY, description="Expectation identity; must be 'foreign_key'."
    )
    child: FieldSelection = Field(description="Referencing field selected from product or declared-sink rows.")
    parent: FieldSelection = Field(description="Referenced field whose captured values form the valid key set.")


class AllowedValuesExpectation(AuthoringModel):
    """Require every captured field value to belong to one explicit accepted vocabulary."""

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "allowed_values",
        "subject": {"kind": "product", "product": "orders"},
        "field": "status",
        "values": ["new", "paid"],
    }

    kind: Literal[ExpectationIntentKind.ALLOWED_VALUES] = Field(
        default=ExpectationIntentKind.ALLOWED_VALUES, description="Expectation identity; must be 'allowed_values'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink row set containing the field.")
    field: NonEmptyStrictStr = Field(description="Field restricted to the declared value set.")
    values: tuple[JsonValue, ...] = Field(min_length=1, description="Complete set of accepted captured values.")


class RangeExpectation(AuthoringModel):
    """Require every captured numeric field value to remain inside inclusive bounds."""

    model_config = ConfigDict(json_schema_extra=_publish_alias_choices)

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "range",
        "subject": {"kind": "product", "product": "orders"},
        "field": "amount",
        "minimum": "0",
        "maximum": "10000",
    }

    kind: Literal[ExpectationIntentKind.RANGE] = Field(
        default=ExpectationIntentKind.RANGE, description="Expectation identity; must be 'range'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink row set containing the numeric field.")
    field: NonEmptyStrictStr = Field(description="Numeric field whose captured values are bounded.")
    # min and max are accepted because the <key> attributes of the same bounds are spelled so.
    minimum: Decimal = Field(
        validation_alias=AliasChoices("minimum", "min"),
        description="Inclusive accepted lower bound; min is the same field.",
    )
    maximum: Decimal = Field(
        validation_alias=AliasChoices("maximum", "max"),
        description="Inclusive accepted upper bound; max is the same field.",
    )

    @model_validator(mode="after")
    def ordered_bounds(self) -> RangeExpectation:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class FixedValueExpectation(AuthoringModel):
    """Require every captured field value to equal one JSON literal."""

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "fixed_value",
        "subject": {"kind": "product", "product": "orders"},
        "field": "currency",
        "value": "EUR",
    }

    kind: Literal[ExpectationIntentKind.FIXED_VALUE] = Field(
        default=ExpectationIntentKind.FIXED_VALUE, description="Expectation identity; must be 'fixed_value'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink row set containing the field.")
    field: NonEmptyStrictStr = Field(description="Field required to equal the declared value.")
    value: JsonValue = Field(description="Exact JSON value required in every captured row.")


class FieldPresentExpectation(AuthoringModel):
    """Require every captured row to contain one declared field."""

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "field_present",
        "subject": {"kind": "product", "product": "orders"},
        "field": "payment_id",
    }

    kind: Literal[ExpectationIntentKind.FIELD_PRESENT] = Field(
        default=ExpectationIntentKind.FIELD_PRESENT, description="Expectation identity; must be 'field_present'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink rows requiring the field.")
    field: NonEmptyStrictStr = Field(description="Field required in every captured row.")


class FieldAbsentExpectation(AuthoringModel):
    """Require every captured row to omit one forbidden field."""

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "field_absent",
        "subject": {"kind": "product", "product": "orders"},
        "field": "legacy_flag",
    }

    kind: Literal[ExpectationIntentKind.FIELD_ABSENT] = Field(
        default=ExpectationIntentKind.FIELD_ABSENT, description="Expectation identity; must be 'field_absent'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink rows that must omit the field.")
    field: NonEmptyStrictStr = Field(description="Field forbidden in every captured row.")


class RowConditionExpectation(AuthoringModel):
    """Require every captured product row to satisfy one boolean business expression."""

    usage_example: ClassVar[dict[str, JsonValue]] = {
        "kind": "row_condition",
        "subject": {"kind": "product", "product": "orders"},
        "condition": "amount >= 0 and currency == 'EUR'",
    }

    kind: Literal[ExpectationIntentKind.ROW_CONDITION] = Field(
        default=ExpectationIntentKind.ROW_CONDITION, description="Expectation identity; must be 'row_condition'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink rows evaluated by the condition.")
    condition: NonEmptyStrictStr = Field(
        description=(
            "Closed Boolean expression over captured fields, comparisons, arithmetic and literal containers. "
            "Use field names and nested mapping access; len(value) is the only supported function. "
            "Arbitrary Python calls such as str() and isinstance() are not supported. " + ROW_CONDITION_GRAMMAR
        ),
        examples=["amount >= 0 and amount <= 100", "len(addresses) == 2"],
    )
    result_type: Literal["bool", "boolean"] = Field(
        default="bool", description='Result type of the row condition; "boolean" is the same as "bool".'
    )

    @field_validator("result_type")
    @classmethod
    def one_boolean_name(cls, value: str) -> Literal["bool"]:
        return "bool"

    @field_validator("condition")
    @classmethod
    def condition_uses_the_closed_row_grammar(cls, value: str) -> str:
        parse_row_condition(value)
        return value


ExpectationIntent = Annotated[
    ExactCountExpectation
    | PerParentCountExpectation
    | UniqueExpectation
    | ForeignKeyExpectation
    | AllowedValuesExpectation
    | RangeExpectation
    | FixedValueExpectation
    | FieldPresentExpectation
    | FieldAbsentExpectation
    | RowConditionExpectation,
    Field(discriminator="kind"),
]
ExpectationSubject = ProductRowsSubject | PerParentRowsSubject | DeclaredSinkRowsSubject
_MODELS = {model.model_fields["kind"].default: model for model in get_args(get_args(ExpectationIntent)[0])}


def expectation_example(kind: ExpectationIntentKind) -> dict[str, JsonValue]:
    return _MODELS[kind].usage_example


# The keys that agents write for the products of a per-parent count.
_PER_PARENT_KEYS = (("subject",), ("parent",), ("child",), ("parent_field",), ("child_field",))


def expectation_repair(location: tuple[str | int, ...]) -> str | None:
    """The shape of the expectation kind a validation location names, and the field to rename when the location
    is a known wrong name; None outside an expectation. Locations hold field names only, never values."""
    kinds = {kind.value: kind for kind in ExpectationIntentKind}
    for index in range(1, len(location)):
        before, part = location[index - 1], location[index]
        # The kind is the union tag right after an item of "expectations" or after an "expectation" field.
        tagged = before == "expectation" or (
            isinstance(before, int) and location[index - 2 : index - 1] == ("expectations",)
        )
        if not tagged or not isinstance(part, str) or part not in kinds:
            continue
        kind = kinds[part]
        model = _MODELS[kind]
        rename = ""
        rest = location[index + 1 :]
        # Only a misplaced product names the side shape; a field typo beside a right subject gets the plain shape.
        side_key = rest[1] if len(rest) > 1 and rest[0] in ("child", "parent") else None
        if kind is ExpectationIntentKind.FOREIGN_KEY and side_key in ("product", "kind", "subject"):
            side = rest[0]
            rename = (
                f"Put the product of {side} inside subject: "
                f'"{side}": {{"subject": {{"kind": "product", "product": "<product>"}}, "field": "<field>"}}. '
            )
        elif kind is ExpectationIntentKind.PER_PARENT_COUNT and rest[:1] in _PER_PARENT_KEYS:
            rename = (
                'Put both products inside subject: "subject": {"kind": "per_parent", "parent_product": "<parent>", '
                '"child_product": "<child>"}; the child must be a nested <generate> inside the parent, and its rows '
                "are grouped by that nesting, so no field names the grouping. "
            )
        elif kind is ExpectationIntentKind.ROW_CONDITION and rest == ("result_type",):
            rename = "Omit result_type: a row condition is always boolean. "
        elif rest:
            wrong = rest[0]
            for name in model.model_fields:
                field = model.model_fields[name]
                extra = field.json_schema_extra
                aliases = extra[INTENT_REPAIR_ALIASES_SCHEMA_KEY] if isinstance(extra, dict) else None
                alias = field.validation_alias
                if isinstance(alias, AliasChoices) and wrong != name and wrong in alias.choices:
                    # An accepted spelling is extra only beside the field name.
                    rename = f"Write only one of {wrong} and {name}. "
                elif isinstance(aliases, list) and wrong in aliases:
                    rename = f"Rename {wrong} to {name}. "
        shape = json.dumps(model.usage_example)
        return f"{rename}A {kind.value} expectation has this shape: {shape}"
    return None


def expectation_subjects(expectation: ExpectationIntent) -> tuple[ExpectationSubject, ...]:
    """Return every row-set subject addressed by an expectation."""
    if isinstance(expectation, ForeignKeyExpectation):
        return (expectation.child.subject, expectation.parent.subject)
    return (expectation.subject,)


def expectation_identity(expectation: ExpectationIntent) -> tuple[object, ...]:
    """Return the complete semantic identity for an acceptance expectation."""
    if isinstance(expectation, ExactCountExpectation):
        return (expectation.kind, _subject_identity(expectation.subject), expectation.count)
    if isinstance(expectation, PerParentCountExpectation):
        return (expectation.kind, _subject_identity(expectation.subject), expectation.count)
    if isinstance(expectation, UniqueExpectation):
        return (expectation.kind, _subject_identity(expectation.subject), expectation.field, expectation.scope)
    if isinstance(expectation, ForeignKeyExpectation):
        return (
            expectation.kind,
            _subject_identity(expectation.child.subject),
            expectation.child.field,
            _subject_identity(expectation.parent.subject),
            expectation.parent.field,
        )
    if isinstance(expectation, AllowedValuesExpectation):
        values = tuple(
            sorted(
                {
                    json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
                    for value in expectation.values
                }
            )
        )
        return (expectation.kind, _subject_identity(expectation.subject), expectation.field, values)
    if isinstance(expectation, RangeExpectation):
        return (
            expectation.kind,
            _subject_identity(expectation.subject),
            expectation.field,
            expectation.minimum,
            expectation.maximum,
        )
    if isinstance(expectation, FixedValueExpectation):
        value = json.dumps(expectation.value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        return (expectation.kind, _subject_identity(expectation.subject), expectation.field, value)
    if isinstance(expectation, FieldPresentExpectation | FieldAbsentExpectation):
        return (expectation.kind, _subject_identity(expectation.subject), expectation.field)
    if isinstance(expectation, RowConditionExpectation):
        return (
            expectation.kind,
            _subject_identity(expectation.subject),
            expectation.condition,
            expectation.result_type,
        )
    raise TypeError(f"unsupported expectation kind {expectation.kind!r}")


def _subject_identity(subject: AuthoringModel) -> str:
    return json.dumps(subject.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
