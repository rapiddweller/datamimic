# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from __future__ import annotations

import json
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, JsonValue, field_validator, model_validator

from .common import AuthoringModel, NonEmptyStrictStr, NonNegativeStrictInt
from .row_conditions import ROW_CONDITION_GRAMMAR, parse_row_condition

INTENT_REPAIR_ALIASES_SCHEMA_KEY = "x-datamimic-repair-aliases"


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

    kind: Literal[ExpectationIntentKind.PER_PARENT_COUNT] = Field(
        default=ExpectationIntentKind.PER_PARENT_COUNT, description="Expectation identity; must be 'per_parent_count'."
    )
    subject: PerParentRowsSubject = Field(description="Nested child rows partitioned by immediate parent row.")
    count: NonNegativeStrictInt = Field(description="Exact child rows expected for each parent row.")


class UniqueExpectation(AuthoringModel):
    """Require captured field values to be unique within one explicit row-set subject."""

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

    kind: Literal[ExpectationIntentKind.FOREIGN_KEY] = Field(
        default=ExpectationIntentKind.FOREIGN_KEY, description="Expectation identity; must be 'foreign_key'."
    )
    child: FieldSelection = Field(description="Referencing field selected from product or declared-sink rows.")
    parent: FieldSelection = Field(description="Referenced field whose captured values form the valid key set.")


class AllowedValuesExpectation(AuthoringModel):
    """Require every captured field value to belong to one explicit accepted vocabulary."""

    kind: Literal[ExpectationIntentKind.ALLOWED_VALUES] = Field(
        default=ExpectationIntentKind.ALLOWED_VALUES, description="Expectation identity; must be 'allowed_values'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink row set containing the field.")
    field: NonEmptyStrictStr = Field(description="Field restricted to the declared value set.")
    values: tuple[JsonValue, ...] = Field(min_length=1, description="Complete set of accepted captured values.")


class RangeExpectation(AuthoringModel):
    """Require every captured numeric field value to remain inside inclusive bounds."""

    kind: Literal[ExpectationIntentKind.RANGE] = Field(
        default=ExpectationIntentKind.RANGE, description="Expectation identity; must be 'range'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink row set containing the numeric field.")
    field: NonEmptyStrictStr = Field(description="Numeric field whose captured values are bounded.")
    minimum: Decimal = Field(description="Inclusive accepted lower bound.")
    maximum: Decimal = Field(description="Inclusive accepted upper bound.")

    @model_validator(mode="after")
    def ordered_bounds(self) -> RangeExpectation:
        if self.minimum > self.maximum:
            raise ValueError("minimum must not exceed maximum")
        return self


class FixedValueExpectation(AuthoringModel):
    """Require every captured field value to equal one JSON literal."""

    kind: Literal[ExpectationIntentKind.FIXED_VALUE] = Field(
        default=ExpectationIntentKind.FIXED_VALUE, description="Expectation identity; must be 'fixed_value'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink row set containing the field.")
    field: NonEmptyStrictStr = Field(description="Field required to equal the declared value.")
    value: JsonValue = Field(description="Exact JSON value required in every captured row.")


class FieldPresentExpectation(AuthoringModel):
    """Require every captured row to contain one declared field."""

    kind: Literal[ExpectationIntentKind.FIELD_PRESENT] = Field(
        default=ExpectationIntentKind.FIELD_PRESENT, description="Expectation identity; must be 'field_present'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink rows requiring the field.")
    field: NonEmptyStrictStr = Field(description="Field required in every captured row.")


class FieldAbsentExpectation(AuthoringModel):
    """Require every captured row to omit one forbidden field."""

    kind: Literal[ExpectationIntentKind.FIELD_ABSENT] = Field(
        default=ExpectationIntentKind.FIELD_ABSENT, description="Expectation identity; must be 'field_absent'."
    )
    subject: ProductOrSinkSubject = Field(description="Product or declared-sink rows that must omit the field.")
    field: NonEmptyStrictStr = Field(description="Field forbidden in every captured row.")


class RowConditionExpectation(AuthoringModel):
    """Require every captured product row to satisfy one boolean business expression."""

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
    result_type: Literal["bool"] = Field(default="bool", description="Required result type of the row condition.")

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
