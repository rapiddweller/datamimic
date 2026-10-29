# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Serializable acceptance facts; no compiler, runtime or sampled-row dependency."""

from __future__ import annotations

import ast
from typing import Literal

from pydantic import model_validator

from .build_rules import catalog_diagnostic
from .common import MAX_AUTHORING_MAX_COUNT, AuthoringModel, NonEmptyStrictStr, NonNegativeStrictInt
from .diagnostics import AuthoringRuleId, Diagnostic, DiagnosticPhase
from .expectations import (
    DeclaredSinkIdentity,
    DeclaredSinkRowsSubject,
    ExactCountExpectation,
    ExpectationIntent,
    FieldAbsentExpectation,
    ForeignKeyExpectation,
    PerParentCountExpectation,
    PerParentRowsSubject,
    ProductRowsSubject,
    RowConditionExpectation,
    expectation_subjects,
)
from .proof import AcceptanceOrigin
from .requests import DEFAULT_AUTHORING_MAX_COUNT
from .row_conditions import parse_row_condition

# On the nest route blind agents wrote max_count 1, and parent.<field> into the count (campaign b5, e06).
BRACES_COUNT_MAX_COUNT = (
    f"A braces count stops Build from deriving max_count, and without max_count Build stops at "
    f'{DEFAULT_AUTHORING_MAX_COUNT} rows: set "max_count" at the top level of acceptance/build.json to the rows of '
    f"all products together; {MAX_AUTHORING_MAX_COUNT} is safe."
)


def nested_count_scope(parent_field: str) -> str:
    """The count rule of a nested <generate>, with a field of the parent row in the example."""
    return (
        "A nested braces count runs in the parent row: it counts the child rows for each parent row and names the "
        f"parent's fields bare, count=\"{{1 if {parent_field} % 2 == 1 else 0}}\"; only the child's keys write "
        "parent.<field>."
    )


def memstore_readback_once(parent_field: str) -> str:
    """The readback rule and the nest route; ``parent_field`` names a field of the producer in the count example."""
    return (
        "A memstore readback reads every producer row exactly once, so its count is the producer count. For a "
        "subset of the rows, or for rows that belong to one parent, nest the child <generate> under the parent "
        f"and copy parent.<field> instead. {nested_count_scope(parent_field)} {BRACES_COUNT_MAX_COUNT}"
    )


MEMSTORE_READBACK_ONCE = memstore_readback_once("id")
# Script scope names that a row condition does not have; an agent writes this.field from the scripts.
_SCRIPT_SCOPES = frozenset(("this", "parent", "root"))


class AcceptanceProjectionError(ValueError):
    def __init__(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        self.diagnostics = diagnostics
        super().__init__(diagnostics[0].message)


class AcceptanceJoinV1(AuthoringModel):
    child_field: NonEmptyStrictStr
    parent_field: NonEmptyStrictStr


class AcceptanceRelationshipV1(AuthoringModel):
    parent_product: NonEmptyStrictStr
    child_product: NonEmptyStrictStr
    joins: tuple[AcceptanceJoinV1, ...] = ()


class AcceptanceListV1(AuthoringModel):
    name: NonEmptyStrictStr
    fields: tuple[NonEmptyStrictStr, ...] = ()
    count_per_row: NonNegativeStrictInt | None = None


class AcceptanceProductV1(AuthoringModel):
    name: NonEmptyStrictStr
    runtime_name: NonEmptyStrictStr
    capture_name: NonEmptyStrictStr
    count_per_invocation: NonNegativeStrictInt | None = None
    fields: tuple[NonEmptyStrictStr, ...] = ()
    lists: tuple[AcceptanceListV1, ...] = ()
    declared_sinks: tuple[DeclaredSinkIdentity, ...] = ()


class AcceptanceCheckV1(AuthoringModel):
    expectation: ExpectationIntent
    path: tuple[str | int, ...]
    origin: AcceptanceOrigin = AcceptanceOrigin.MODEL


class AcceptanceReadbackV1(AuthoringModel):
    producer: NonEmptyStrictStr
    consumer: NonEmptyStrictStr
    producer_field: NonEmptyStrictStr
    consumer_field: NonEmptyStrictStr
    path: tuple[str | int, ...]


class AcceptanceSpecV1(AuthoringModel):
    version: Literal["1"] = "1"
    products: tuple[AcceptanceProductV1, ...]
    relationships: tuple[AcceptanceRelationshipV1, ...] = ()
    checks: tuple[AcceptanceCheckV1, ...] = ()
    readbacks: tuple[AcceptanceReadbackV1, ...] = ()
    # The rows of all products together; None when a product has no literal count (a source, a script count).
    declared_rows: NonNegativeStrictInt | None = None

    def product(self, name: str) -> AcceptanceProductV1 | None:
        return next((product for product in self.products if product.name == name), None)

    def declared_sink_contributors(self) -> dict[DeclaredSinkIdentity, tuple[str, ...]]:
        grouped: dict[DeclaredSinkIdentity, list[str]] = {}
        for product in self.products:
            for sink in product.declared_sinks:
                grouped.setdefault(sink, []).append(product.name)
        return {sink: tuple(names) for sink, names in grouped.items()}

    def join_fields(self, child_product: str, parent_product: str) -> tuple[str, str] | None:
        relationship = next(
            (
                item
                for item in self.relationships
                if item.child_product == child_product and item.parent_product == parent_product
            ),
            None,
        )
        if relationship is None or len(relationship.joins) != 1:
            return None
        join = relationship.joins[0]
        return join.child_field, join.parent_field

    @model_validator(mode="after")
    def validate_graph(self) -> AcceptanceSpecV1:
        names = [product.name for product in self.products]
        runtime_names = [product.runtime_name for product in self.products]
        capture_names = [product.capture_name for product in self.products]
        if (
            len(names) != len(set(names))
            or len(runtime_names) != len(set(runtime_names))
            or len(capture_names) != len(set(capture_names))
        ):
            raise ValueError("acceptance product and runtime names must be unique")
        for product in self.products:
            if len(product.fields) != len(set(product.fields)):
                raise ValueError("acceptance fields must be unique")
        for relationship in self.relationships:
            parent, child = self.product(relationship.parent_product), self.product(relationship.child_product)
            if parent is None or child is None:
                raise ValueError("acceptance relationship references an unknown product")
            if any(
                join.parent_field not in parent.fields or join.child_field not in child.fields
                for join in relationship.joins
            ):
                raise ValueError("acceptance relationship references an unknown field")
        for readback in self.readbacks:
            producer, consumer = self.product(readback.producer), self.product(readback.consumer)
            if (
                producer is None
                or consumer is None
                or readback.producer_field not in producer.fields
                or readback.consumer_field not in consumer.fields
            ):
                raise ValueError("acceptance readback references an unknown product or field")
        for check in self.checks:
            validate_acceptance_check(self, check)
        return self


def _reject(
    message: str,
    path: tuple[str | int, ...],
    remediation: str | None = None,
    declared: tuple[str, ...] | None = None,
) -> None:
    """``declared`` lists the structural names the reference can take: products or fields, never row values."""
    raise AcceptanceProjectionError(
        (
            catalog_diagnostic(
                AuthoringRuleId.INPUT,
                message,
                phase=DiagnosticPhase.EXPECTATION,
                path=path,
                allowed_values=declared,
                remediation=remediation,
            ),
        )
    )


def validate_acceptance_subject(
    spec: AcceptanceSpecV1,
    subject: ProductRowsSubject | PerParentRowsSubject | DeclaredSinkRowsSubject,
    path: tuple[str | int, ...],
    field: str | None = None,
) -> None:
    names: tuple[str, ...]
    if isinstance(subject, PerParentRowsSubject):
        names = (subject.parent_product, subject.child_product)
        if not any(item.parent_product == names[0] and item.child_product == names[1] for item in spec.relationships):
            _reject("Expectation references a missing nested relationship.", path)
        if field is not None:
            product = spec.product(subject.child_product)
            if product is None or field not in product.fields:
                _reject(
                    "Expectation references an unknown child field.",
                    path + ("field",),
                    declared=product.fields if product is not None else None,
                )
        return
    names = (
        (subject.product,)
        if isinstance(subject, ProductRowsSubject)
        else spec.declared_sink_contributors().get(subject.sink, ())
    )
    if not names:
        _reject("Expectation references a sink without captured contributors.", path)
    for name in names:
        product = spec.product(name)
        if product is None:
            _reject(
                "Expectation references an unknown product.",
                path + ("product",),
                declared=tuple(item.name for item in spec.products),
            )
            return
        fields = product.fields
        owner = "of that product"
        if isinstance(subject, ProductRowsSubject) and subject.list_field is not None:
            selected = next((item for item in product.lists if item.name == subject.list_field), None)
            if selected is None:
                _reject("Expectation references an unknown list field.", path + ("list_field",))
                return
            fields = selected.fields
            owner = 'inside the <nestedKey type="list"> that list_field names'
        if field is not None and field not in fields:
            _reject(
                "Expectation references an unknown field.",
                path + ("field",),
                remediation=(
                    f"Declare the field as a <key> {owner}; Build knows only declared keys, not fields that "
                    "appear only in rows a script or source produces."
                ),
                declared=fields,
            )


def validate_acceptance_check(spec: AcceptanceSpecV1, check: AcceptanceCheckV1) -> None:
    expectation = check.expectation
    for subject in expectation_subjects(expectation):
        validate_acceptance_subject(spec, subject, check.path + ("subject",))
    if isinstance(expectation, ForeignKeyExpectation):
        validate_acceptance_subject(spec, expectation.child.subject, check.path + ("child",), expectation.child.field)
        validate_acceptance_subject(
            spec, expectation.parent.subject, check.path + ("parent",), expectation.parent.field
        )
    elif isinstance(expectation, RowConditionExpectation):
        tree = parse_row_condition(expectation.condition)
        call_functions = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and id(node) not in call_functions:
                try:
                    validate_acceptance_subject(spec, expectation.subject, check.path + ("condition",), node.id)
                except AcceptanceProjectionError:
                    if node.id not in _SCRIPT_SCOPES:
                        raise
                    _reject(
                        "Expectation references an unknown field.",
                        check.path + ("condition", "field"),
                        remediation="A row condition reads one captured row and names its fields bare: write "
                        "price <= 9, not this.price <= 9. this, parent and root belong to scripts.",
                    )
    elif not isinstance(expectation, (ExactCountExpectation, PerParentCountExpectation, FieldAbsentExpectation)):
        validate_acceptance_subject(spec, expectation.subject, check.path, expectation.field)
