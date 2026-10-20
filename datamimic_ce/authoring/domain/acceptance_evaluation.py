# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Runtime-free acceptance evaluation for the current authoring DSL contract."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import assert_never
from uuid import UUID

from pydantic import JsonValue

from datamimic_ce.authoring.domain.acceptance_contract import AcceptanceSpecV1
from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.capture import CapturedObjectId, CapturedProducts, CaptureStatus
from datamimic_ce.authoring.domain.common import MAX_AUTHORING_MAX_COUNT
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, Diagnostic, DiagnosticPhase
from datamimic_ce.authoring.domain.expectations import (
    AllowedValuesExpectation,
    DeclaredSinkRowsSubject,
    ExactCountExpectation,
    ExpectationIntent,
    ExpectationIntentKind,
    FieldAbsentExpectation,
    FieldPresentExpectation,
    FixedValueExpectation,
    ForeignKeyExpectation,
    PerParentCountExpectation,
    PerParentRowsSubject,
    ProductRowsSubject,
    RangeExpectation,
    RowConditionExpectation,
    UniqueExpectation,
    expectation_subjects,
)
from datamimic_ce.authoring.domain.row_conditions import evaluate_row_condition

CapturedRows = Mapping[str, tuple[Mapping[str, object], ...]]


@dataclass(frozen=True)
class _ExpectationFailure:
    message: str
    details: dict[str, object]


def _diagnostic(
    kind: ExpectationIntentKind,
    failure: _ExpectationFailure,
    *,
    path: tuple[str | int, ...],
) -> Diagnostic:
    return catalog_diagnostic(kind, failure.message, phase=DiagnosticPhase.EVIDENCE, path=path).model_copy(
        update=failure.details
    )


def _unevaluable_diagnostic(
    subject: DeclaredSinkRowsSubject,
    missing: tuple[str, ...],
    *,
    path: tuple[str | int, ...],
) -> Diagnostic:
    return catalog_diagnostic(
        AuthoringRuleId.UNEVALUABLE_SINK_EXPECTATION,
        f"{_subject_label(subject)} is missing bounded capture for: {', '.join(missing)}",
        phase=DiagnosticPhase.EVIDENCE,
        path=path,
    ).model_copy(
        update={
            "expected": list(missing),
            "actual": [],
        }
    )


def _rows(captured: CapturedRows, product: str) -> tuple[Mapping[str, object], ...] | None:
    rows = captured.get(product)
    if rows is None:
        return None
    return tuple(rows)


def _subject_rows(
    spec: AcceptanceSpecV1,
    captured: CapturedRows,
    subject: ProductRowsSubject | DeclaredSinkRowsSubject,
) -> tuple[Mapping[str, object], ...] | None:
    if isinstance(subject, ProductRowsSubject):
        rows = _rows(captured, subject.product)
        if rows is None or subject.list_field is None:
            return rows
        flattened: list[Mapping[str, object]] = []
        for row in rows:
            items = row.get(subject.list_field)
            if not isinstance(items, list | tuple) or not all(isinstance(item, Mapping) for item in items):
                return None
            flattened.extend(items)
        return tuple(flattened)
    combined: list[Mapping[str, object]] = []
    for product in spec.declared_sink_contributors().get(subject.sink, ()):
        rows = _rows(captured, product)
        if rows is None:
            return None
        combined.extend(rows)
    return tuple(combined)


def _subject_label(subject: ProductRowsSubject | PerParentRowsSubject | DeclaredSinkRowsSubject) -> str:
    if isinstance(subject, ProductRowsSubject):
        return f"product '{subject.product}'"
    if isinstance(subject, PerParentRowsSubject):
        return f"'{subject.child_product}' per parent '{subject.parent_product}'"
    sink = subject.sink
    return f"declared sink '{sink.kind}:{sink.environment}:{sink.entity}'"


def _unevaluable_sink_subject(
    spec: AcceptanceSpecV1,
    captured: CapturedRows,
    expectation: ExpectationIntent,
) -> tuple[DeclaredSinkRowsSubject, tuple[str, ...]] | None:
    contributors = spec.declared_sink_contributors()
    for subject in expectation_subjects(expectation):
        if not isinstance(subject, DeclaredSinkRowsSubject):
            continue
        missing = tuple(product for product in contributors.get(subject.sink, ()) if _rows(captured, product) is None)
        if missing:
            return subject, missing
    return None


def declared_sink_coverage_warnings(spec: AcceptanceSpecV1) -> tuple[Diagnostic, ...]:
    """Report structurally visible multi-product sinks without explicit sink assurance."""
    assured = {
        subject.sink
        for check in spec.checks
        for expectation in (check.expectation,)
        for subject in expectation_subjects(expectation)
        if isinstance(subject, DeclaredSinkRowsSubject)
    }
    diagnostics: list[Diagnostic] = []
    for sink, contributors in spec.declared_sink_contributors().items():
        if len(contributors) < 2 or sink in assured:
            continue
        diagnostic = catalog_diagnostic(
            AuthoringRuleId.UNASSURED_MULTI_CONTRIBUTOR_SINK,
            (
                f"{len(contributors)} products contribute to declared sink "
                f"'{sink.kind}:{sink.environment}:{sink.entity}' without sink-scoped assurance"
            ),
            phase=DiagnosticPhase.EXPECTATION,
            path=("products",),
        ).model_copy(
            update={
                "expected": {"declared_sink_expectations": "at_least_one"},
                "actual": {
                    "sink": sink.model_dump(mode="json"),
                    "contributors": list(contributors),
                    "declared_sink_expectations": 0,
                },
            }
        )
        diagnostics.append(diagnostic)
    return tuple(diagnostics)


def _values(rows: tuple[Mapping[str, object], ...], field: str) -> tuple[object, ...] | None:
    values: list[object] = []
    for row in rows:
        if field not in row:
            return None
        values.append(row[field])
    return tuple(values)


def _typed_identity(value: object) -> JsonValue:
    content: JsonValue
    if isinstance(value, Mapping):
        content = {str(key): _typed_identity(item) for key, item in value.items()}
    elif isinstance(value, tuple | list):
        content = [_typed_identity(item) for item in value]
    else:
        content = _json_value(value)
    return [type(value).__name__, content]


def _display(value: object) -> str:
    return json.dumps(_typed_identity(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _json_value(value: object) -> JsonValue:
    if isinstance(value, CapturedObjectId):
        return value.value
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Decimal | date | datetime | UUID):
        return str(value)
    if isinstance(value, tuple | list):
        return [_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    raise TypeError("Unsupported capture value")


def _duplicate_values(values: tuple[object, ...]) -> tuple[object, ...]:
    seen: set[str] = set()
    duplicates: list[object] = []
    for value in values:
        key = _display(value)
        if key in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(key)
    return tuple(duplicates)


def _groups(
    spec: AcceptanceSpecV1,
    captured: CapturedRows,
    child_product: str,
    parent_product: str,
) -> dict[str, tuple[Mapping[str, object], ...]] | None:
    child_rows = _rows(captured, child_product)
    parent_rows = _rows(captured, parent_product)
    if child_rows is None or parent_rows is None:
        return None
    join = spec.join_fields(child_product, parent_product)
    if join is None:
        return None
    child_field, parent_field = join
    child_values = _values(child_rows, child_field)
    parent_values = _values(parent_rows, parent_field)
    if child_values is None or parent_values is None or len(set(map(_display, parent_values))) != len(parent_values):
        return None
    groups: dict[str, list[Mapping[str, object]]] = {_display(value): [] for value in parent_values}
    for row, value in zip(child_rows, child_values, strict=True):
        group = groups.get(_display(value))
        if group is None:
            return None
        group.append(row)
    return {key: tuple(value) for key, value in groups.items()}


def _decimal(value: object) -> Decimal | None:
    try:
        if isinstance(value, bool):
            return None
        number = Decimal(str(value))
        return number if number.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def _check_expectation(
    spec: AcceptanceSpecV1,
    captured: CapturedRows,
    expectation: ExpectationIntent,
) -> _ExpectationFailure | None:
    if isinstance(expectation, ExactCountExpectation):
        rows = _subject_rows(spec, captured, expectation.subject)
        if rows is None:
            return _ExpectationFailure(
                f"captured {_subject_label(expectation.subject)} is incomplete",
                {"expected": expectation.count, "actual": None},
            )
        if len(rows) != expectation.count:
            return _ExpectationFailure(
                f"expected {expectation.count} rows for {_subject_label(expectation.subject)} but observed {len(rows)}",
                {"expected": expectation.count, "actual": len(rows)},
            )
        return None
    if isinstance(expectation, PerParentCountExpectation):
        subject = expectation.subject
        parent_groups = _groups(spec, captured, subject.child_product, subject.parent_product)
        if parent_groups is None:
            return _ExpectationFailure(
                f"could not group '{subject.child_product}' by '{subject.parent_product}'",
                {"expected": expectation.count, "actual": None},
            )
        counts = {parent: len(rows) for parent, rows in parent_groups.items()}
        if any(count != expectation.count for count in counts.values()):
            return _ExpectationFailure(
                f"expected {expectation.count} child rows per parent for '{subject.child_product}'",
                {"expected": expectation.count, "actual": counts},
            )
        return None
    if isinstance(expectation, UniqueExpectation):
        unique_subject = expectation.subject
        if (
            isinstance(unique_subject, ProductRowsSubject)
            and unique_subject.list_field
            and expectation.scope == "per_parent"
        ):
            root_rows = _rows(captured, unique_subject.product)
            if root_rows is None:
                return _ExpectationFailure("Nested-list capture is missing.", {"actual": None})
            for row in root_rows:
                items = row.get(unique_subject.list_field)
                if not isinstance(items, list | tuple) or not all(isinstance(item, Mapping) for item in items):
                    return _ExpectationFailure("Nested-list capture is invalid.", {"actual": None})
                values = _values(tuple(items), expectation.field)
                if values is None or _duplicate_values(values):
                    return _ExpectationFailure(
                        "Nested-list values are not unique within each root row.", {"expected": "unique_per_parent"}
                    )
            return None
        if isinstance(unique_subject, ProductRowsSubject) and expectation.scope == "per_parent":
            relationship = next(
                (item for item in spec.relationships if item.child_product == unique_subject.product), None
            )
            if relationship is None:
                return _ExpectationFailure("Per-parent uniqueness requires a nested product or list.", {"actual": None})
            return _check_expectation(
                spec,
                captured,
                UniqueExpectation(
                    subject=PerParentRowsSubject(
                        parent_product=relationship.parent_product, child_product=relationship.child_product
                    ),
                    field=expectation.field,
                ),
            )
        if isinstance(unique_subject, ProductRowsSubject | DeclaredSinkRowsSubject):
            rows = _subject_rows(spec, captured, unique_subject)
            if rows is None:
                return _ExpectationFailure(
                    f"captured {_subject_label(unique_subject)} is incomplete",
                    {"expected": "unique", "actual": None},
                )
            values = _values(rows, expectation.field)
            if values is None:
                return _ExpectationFailure(
                    f"field '{expectation.field}' is missing from {_subject_label(unique_subject)}",
                    {"expected": "unique", "actual": None},
                )
            duplicates = _duplicate_values(values)
            if duplicates:
                return _ExpectationFailure(
                    f"duplicate values captured for '{expectation.field}' in {_subject_label(unique_subject)}",
                    {"expected": "unique", "actual": _json_value(duplicates)},
                )
            return None
        groups_by_parent = _groups(
            spec,
            captured,
            unique_subject.child_product,
            unique_subject.parent_product,
        )
        if groups_by_parent is None:
            return _ExpectationFailure(
                f"captured {_subject_label(unique_subject)} is incomplete",
                {"expected": "unique_per_parent", "actual": None},
            )
        duplicates_by_parent: dict[str, object] = {}
        for parent, group in groups_by_parent.items():
            values = _values(group, expectation.field)
            if values is None:
                return _ExpectationFailure(
                    f"field '{expectation.field}' is missing from {_subject_label(unique_subject)}",
                    {"expected": "unique_per_parent", "actual": None},
                )
            duplicates = _duplicate_values(values)
            if duplicates:
                duplicates_by_parent[parent] = _json_value(duplicates)
        if duplicates_by_parent:
            return _ExpectationFailure(
                f"duplicate values captured for '{expectation.field}' in {_subject_label(unique_subject)}",
                {"expected": "unique_per_parent", "actual": duplicates_by_parent},
            )
        return None
    if isinstance(expectation, ForeignKeyExpectation):
        child_rows = _subject_rows(spec, captured, expectation.child.subject)
        parent_rows = _subject_rows(spec, captured, expectation.parent.subject)
        child_values = _values(child_rows, expectation.child.field) if child_rows is not None else None
        parent_values = _values(parent_rows, expectation.parent.field) if parent_rows is not None else None
        if child_values is None or parent_values is None:
            return _ExpectationFailure(
                f"foreign-key capture is incomplete for {_subject_label(expectation.child.subject)}",
                {"expected": "captured parent keys", "actual": None},
            )
        parent_keys = {_display(value) for value in parent_values}
        orphans = tuple(value for value in child_values if _display(value) not in parent_keys)
        if orphans:
            return _ExpectationFailure(
                f"foreign-key values for '{expectation.child.field}' have no parent",
                {"expected": _json_value(parent_values), "actual": _json_value(orphans)},
            )
        return None
    if isinstance(expectation, AllowedValuesExpectation):
        rows = _subject_rows(spec, captured, expectation.subject)
        values = _values(rows or (), expectation.field) if rows is not None else None
        allowed = tuple(_json_value(value) for value in expectation.values)
        if values is None:
            return _ExpectationFailure(
                f"field '{expectation.field}' is missing from {_subject_label(expectation.subject)}",
                {"expected": list(allowed), "actual": None, "allowed_values": allowed},
            )
        invalid = tuple(
            value for value in values if _display(value) not in {_display(item) for item in expectation.values}
        )
        if invalid:
            return _ExpectationFailure(
                f"unexpected values captured for '{expectation.field}' in {_subject_label(expectation.subject)}",
                {"expected": list(allowed), "actual": _json_value(invalid), "allowed_values": allowed},
            )
        return None
    if isinstance(expectation, RangeExpectation):
        rows = _subject_rows(spec, captured, expectation.subject)
        values = _values(rows or (), expectation.field) if rows is not None else None
        expected = {"minimum": str(expectation.minimum), "maximum": str(expectation.maximum)}
        if values is None:
            return _ExpectationFailure(
                f"field '{expectation.field}' is missing from {_subject_label(expectation.subject)}",
                {"expected": expected, "actual": None},
            )
        invalid = tuple(
            value
            for value in values
            if (number := _decimal(value)) is None or not expectation.minimum <= number <= expectation.maximum
        )
        if invalid:
            return _ExpectationFailure(
                f"values for '{expectation.field}' in {_subject_label(expectation.subject)} are outside the range",
                {"expected": expected, "actual": _json_value(invalid)},
            )
        return None
    if isinstance(expectation, FixedValueExpectation):
        rows = _subject_rows(spec, captured, expectation.subject)
        values = _values(rows or (), expectation.field) if rows is not None else None
        if values is None:
            return _ExpectationFailure(
                f"field '{expectation.field}' is missing from {_subject_label(expectation.subject)}",
                {"expected": _json_value(expectation.value), "actual": None},
            )
        invalid = tuple(value for value in values if _display(value) != _display(expectation.value))
        if invalid:
            return _ExpectationFailure(
                f"values for '{expectation.field}' in {_subject_label(expectation.subject)} do not match",
                {"expected": _json_value(expectation.value), "actual": _json_value(invalid)},
            )
        return None
    if isinstance(expectation, FieldPresentExpectation):
        rows = _subject_rows(spec, captured, expectation.subject)
        if rows is None:
            return _ExpectationFailure(
                f"captured {_subject_label(expectation.subject)} is incomplete",
                {"expected": True, "actual": None},
            )
        mismatches = [index for index, row in enumerate(rows) if expectation.field not in row]
        if mismatches:
            return _ExpectationFailure(
                f"field '{expectation.field}' is missing from {_subject_label(expectation.subject)}",
                {"expected": True, "actual": mismatches},
            )
        return None
    if isinstance(expectation, FieldAbsentExpectation):
        rows = _subject_rows(spec, captured, expectation.subject)
        if rows is None:
            return _ExpectationFailure(
                f"captured {_subject_label(expectation.subject)} is incomplete",
                {"expected": False, "actual": None},
            )
        mismatches = [index for index, row in enumerate(rows) if expectation.field in row]
        if mismatches:
            return _ExpectationFailure(
                f"field '{expectation.field}' is present in {_subject_label(expectation.subject)}",
                {"expected": False, "actual": mismatches},
            )
        return None
    if isinstance(expectation, RowConditionExpectation):
        rows = _subject_rows(spec, captured, expectation.subject)
        if rows is None:
            return _ExpectationFailure(
                f"captured {_subject_label(expectation.subject)} is incomplete",
                {"expected": expectation.condition, "actual": None},
            )
        try:
            failures = [
                index for index, row in enumerate(rows) if not evaluate_row_condition(expectation.condition, row)
            ]
        except (ArithmeticError, TypeError, ValueError):
            return _ExpectationFailure(
                f"row condition could not be evaluated for {_subject_label(expectation.subject)}",
                {"expected": expectation.condition, "actual": None},
            )
        if failures:
            return _ExpectationFailure(
                f"row condition failed for {_subject_label(expectation.subject)}",
                {"expected": expectation.condition, "actual": failures},
            )
        return None
    assert_never(expectation)


def _retry_remediation(count: int) -> str:
    return f"Increase max_count to at least {count} and retry the same transaction."


def _incomplete_capture_remediation(status: CaptureStatus) -> str:
    if status is CaptureStatus.CAPPED:
        return (
            "Give the product a literal count, minCount/maxCount with a static upper bound, or a finite source "
            "within max_count; a capped capture cannot prove completeness."
        )
    return "Declare a literal count or a finite source so the bounded capture can prove completeness."


def _capture_failure(message: str, path: tuple[str | int, ...]) -> Diagnostic:
    return catalog_diagnostic(AuthoringRuleId.VALIDATION, message, phase=DiagnosticPhase.EVIDENCE, path=path)


def _valid_json(value: object) -> bool:
    from datamimic_ce.authoring.domain.capture import validate_capture_values

    try:
        validate_capture_values(value)
    except ValueError:
        return False
    return True


def evaluate_acceptance(spec: AcceptanceSpecV1, captured: CapturedProducts) -> tuple[Diagnostic, ...]:
    """Reject incomplete evidence before evaluating any declared or derived check."""
    diagnostics: list[Diagnostic] = []
    names = [product.name for product in captured.products]
    if len(names) != len(set(names)):
        return (_capture_failure("Duplicate capture product identities.", ("evidence",)),)
    unknown = set(names) - {product.capture_name for product in spec.products}
    if unknown:
        return (_capture_failure("Capture contains undeclared product identities.", ("evidence",)),)
    if type(captured.max_count) is not int or captured.max_count < 1:
        return (_capture_failure("Capture bound is invalid.", ("evidence",)),)
    rows_by_name: dict[str, tuple[Mapping[str, object], ...]] = {}
    retry_counts: dict[str, int] = {}
    for product in spec.products:
        item = captured.get(product.capture_name)
        path = ("evidence", product.name)
        if item is None:
            diagnostics.append(_capture_failure("Declared product capture is missing.", path))
            continue
        evidence = item.capture
        if (
            evidence is None
            or not evidence.complete
            or evidence.observed != len(item.rows)
            or evidence.limit < 1
            or evidence.observed > evidence.limit
            or (
                evidence.status is CaptureStatus.COMPLETE
                and evidence.requested is not None
                and evidence.requested != evidence.observed
            )
        ):
            diagnostic = _capture_failure("Product capture is incomplete or its provenance is inconsistent.", path)
            if evidence is not None:
                count = product.count_per_invocation
                retry = (
                    evidence.status is CaptureStatus.CAPPED
                    and evidence.observed == len(item.rows) == evidence.limit
                    and count is not None
                    and captured.max_count < count <= MAX_AUTHORING_MAX_COUNT
                )
                diagnostic = diagnostic.model_copy(
                    update={
                        "message": f"Product capture is {evidence.status.value}: {evidence.reason}.",
                        "remediation": _retry_remediation(count)
                        if retry and count is not None
                        else _incomplete_capture_remediation(evidence.status),
                        "actual": {
                            "status": evidence.status.value,
                            "requested": evidence.requested,
                            "observed": evidence.observed,
                            "limit": evidence.limit,
                        },
                    }
                )
                if retry and count is not None:
                    retry_counts[product.name] = count
            diagnostics.append(diagnostic)
            continue
        rows: list[Mapping[str, object]] = []
        for index, row in enumerate(item.rows):
            if not isinstance(row, Mapping) or not _valid_json(row):
                diagnostics.append(
                    _capture_failure(
                        "Captured rows must be complete objects with supported data values.", path + (index,)
                    )
                )
                break
            rows.append(row)
            for list_spec in product.lists:
                items = row.get(list_spec.name)
                if not isinstance(items, list | tuple) or not all(isinstance(inner, Mapping) for inner in items):
                    diagnostics.append(
                        _capture_failure("Nested-list capture must contain objects.", path + (index, list_spec.name))
                    )
                elif list_spec.count_per_row is not None and len(items) != list_spec.count_per_row:
                    diagnostics.append(
                        _capture_failure(
                            "Nested-list count differs from its declared count.", path + (index, list_spec.name)
                        )
                    )
        rows_by_name[product.name] = tuple(rows)
    if diagnostics:
        if retry_counts:
            minimum = max(retry_counts.values())
            diagnostics[0] = diagnostics[0].model_copy(
                update={
                    "expected": {
                        "parameter": "max_count",
                        "minimum_value": minimum,
                        "affected_products": sorted(retry_counts),
                    },
                    "remediation": _retry_remediation(minimum),
                }
            )
        return tuple(diagnostics)
    for check in spec.checks:
        expectation = check.expectation
        unevaluable = _unevaluable_sink_subject(spec, rows_by_name, expectation)
        if unevaluable is not None:
            subject, missing = unevaluable
            diagnostics.append(_unevaluable_diagnostic(subject, missing, path=check.path))
            continue
        failure = _check_expectation(spec, rows_by_name, expectation)
        if failure is not None:
            diagnostics.append(_diagnostic(expectation.kind, failure, path=check.path))
    for readback in spec.readbacks:
        producer = _values(rows_by_name[readback.producer], readback.producer_field)
        consumer = _values(rows_by_name[readback.consumer], readback.consumer_field)
        if (
            producer is None
            or consumer is None
            or len(producer) != len(consumer)
            or _duplicate_values(producer)
            or _duplicate_values(consumer)
            or set(map(_display, producer)) != set(map(_display, consumer))
        ):
            diagnostics.append(
                _capture_failure("Memstore readback must preserve every producer identity exactly once.", readback.path)
            )
    return tuple(diagnostics)


__all__ = ["declared_sink_coverage_warnings", "evaluate_acceptance"]
