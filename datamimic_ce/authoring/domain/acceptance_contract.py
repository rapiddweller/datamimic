# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Serializable acceptance facts; no compiler, runtime or sampled-row dependency."""

from __future__ import annotations

import ast
from typing import Literal

from pydantic import model_validator

from .build_rules import catalog_diagnostic
from .common import AuthoringModel, NonEmptyStrictStr, NonNegativeStrictInt
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
from .row_conditions import parse_row_condition


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


def _reject(message: str, path: tuple[str | int, ...], remediation: str | None = None) -> None:
    raise AcceptanceProjectionError(
        (
            catalog_diagnostic(
                AuthoringRuleId.INPUT,
                message,
                phase=DiagnosticPhase.EXPECTATION,
                path=path,
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
                _reject("Expectation references an unknown child field.", path + ("field",))
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
            _reject("Expectation references an unknown product.", path + ("product",))
            return
        fields = product.fields
        if isinstance(subject, ProductRowsSubject) and subject.list_field is not None:
            selected = next((item for item in product.lists if item.name == subject.list_field), None)
            if selected is None:
                _reject("Expectation references an unknown list field.", path + ("list_field",))
                return
            fields = selected.fields
        if field is not None and field not in fields:
            _reject(
                "Expectation references an unknown field.",
                path + ("field",),
                remediation=(
                    "Declare the field as a <key> of that product; Build knows only declared keys, not fields that "
                    "appear only in rows a script or source produces."
                ),
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
                validate_acceptance_subject(spec, expectation.subject, check.path + ("condition",), node.id)
    elif not isinstance(expectation, (ExactCountExpectation, PerParentCountExpectation, FieldAbsentExpectation)):
        validate_acceptance_subject(spec, expectation.subject, check.path, expectation.field)
