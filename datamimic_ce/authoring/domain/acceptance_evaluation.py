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

from datamimic_ce.authoring.domain.acceptance_contract import MEMSTORE_READBACK_ONCE, AcceptanceSpecV1
from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.capture import CapturedObjectId, CapturedProducts, CaptureStatus, binary_evidence
from datamimic_ce.authoring.domain.common import MAX_AUTHORING_MAX_COUNT
from datamimic_ce.authoring.domain.coverage import (
    MAX_LISTED_EXPECTATIONS,
    ExpectationResult,
    ListedExpectation,
    ListedExpectations,
)
from datamimic_ce.authoring.domain.diagnostics import (
    AuthoringRuleId,
    AuthoringSystemDiagnosticCode,
    Diagnostic,
    DiagnosticPhase,
)
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
    expectation_field,
    expectation_subjects,
)
from datamimic_ce.authoring.domain.proof import AcceptanceOrigin
from datamimic_ce.authoring.domain.row_conditions import (
    RowConditionError,
    RowConditionFailure,
    evaluate_row_condition,
    parse_temporal_literal,
)

CapturedRows = Mapping[str, tuple[Mapping[str, object], ...]]


# Build joins a child row to its parent only through one key that copies a unique parent field.
_GROUP_BY_PARENT_COPY = (
    "Build groups the child rows by one child <key> whose script is exactly parent.<field> of a unique parent "
    'field, for example <key name="depot_id" script="parent.depot_id"/>. A copy of a parent <variable> does not '
    "group: the variable is no field of the parent. When the child copies several parent fields, declare a "
    "foreign_key role for the copy that groups."
)


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


def _temporal_literal_matches(actual: date, expected: str) -> bool:
    parsed = parse_temporal_literal(expected)
    # A datetime capture matches a datetime literal only, a date capture a date literal only.
    if isinstance(actual, datetime):
        return isinstance(parsed, datetime) and actual == parsed
    return type(parsed) is date and actual == parsed


def _matches_literal(actual: object, expected: JsonValue) -> bool:
    """One rule for allowed_values and fixed_value (#476): a date or datetime capture matches its ISO literal;
    every other value compares by type and value, so the literal 1 never matches a True capture."""
    if isinstance(actual, date) and isinstance(expected, str):
        return _temporal_literal_matches(actual, expected)
    return _display(actual) == _display(expected)


def _json_value(value: object) -> JsonValue:
    if isinstance(value, bytes):
        return binary_evidence(value)
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


def _readback_identities(rows: tuple[Mapping[str, object], ...], fields: tuple[str, ...]) -> set[str] | None:
    if any(field not in row for row in rows for field in fields):
        return None
    identities = {_display(tuple(row[field] for field in fields)) for row in rows}
    return identities if len(identities) == len(rows) else None


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
                {"expected": expectation.count, "actual": None, "remediation": _GROUP_BY_PARENT_COPY},
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
            value for value in values if not any(_matches_literal(value, item) for item in expectation.values)
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
        non_numeric = tuple(
            value for value in values if isinstance(value, bool) or not isinstance(value, (int, float, Decimal))
        )
        if non_numeric:
            return _ExpectationFailure(
                f"values for '{expectation.field}' in {_subject_label(expectation.subject)} are not numbers; "
                "range requires numeric captured values",
                {"expected": expected, "actual": _json_value(non_numeric)},
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
        invalid = tuple(value for value in values if not _matches_literal(value, expectation.value))
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
        except RowConditionError as error:
            return _unevaluable_row_condition(expectation, error.failure)
        except (ArithmeticError, TypeError, ValueError):
            # Anything the evaluator did not classify: report it without a reason rather than guess one.
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


def _unevaluable_row_condition(
    expectation: RowConditionExpectation, failure: RowConditionFailure
) -> _ExpectationFailure:
    return _ExpectationFailure(
        f"row condition could not be evaluated for {_subject_label(expectation.subject)}: {failure.value}",
        {"expected": expectation.condition, "actual": None},
    )


def _retry_remediation(count: int) -> str:
    return f"Increase max_count to at least {count} and retry the same transaction."


def _incomplete_capture_remediation(status: CaptureStatus) -> str:
    if status is CaptureStatus.CAPPED:
        return (
            "Give the product a literal count, minCount/maxCount with a static upper bound, or a finite source "
            "within max_count; a capped capture cannot prove completeness."
        )
    # UNKNOWN has several causes (memstore producer binding, parent capture, cardinality); the message
    # names the concrete one via capture.reason, so no single cardinality fix may be prescribed here.
    return "Resolve the cause named in the capture reason so the bounded capture can prove completeness."


def _capture_failure(message: str, path: tuple[str | int, ...]) -> Diagnostic:
    return catalog_diagnostic(AuthoringRuleId.VALIDATION, message, phase=DiagnosticPhase.EVIDENCE, path=path)


def _valid_json(value: object) -> bool:
    from datamimic_ce.authoring.domain.capture import validate_capture_values

    try:
        validate_capture_values(value)
    except ValueError:
        return False
    return True


def _expectation_products(spec: AcceptanceSpecV1, expectation: ExpectationIntent) -> set[str]:
    names: set[str] = set()
    contributors = spec.declared_sink_contributors()
    for subject in expectation_subjects(expectation):
        if isinstance(subject, ProductRowsSubject):
            names.add(subject.product)
        elif isinstance(subject, PerParentRowsSubject):
            names.update((subject.parent_product, subject.child_product))
        else:
            names.update(contributors.get(subject.sink, ()))
    return names


def _not_evaluated(spec: AcceptanceSpecV1, not_run: set[str]) -> tuple[tuple[str | int, ...], ...]:
    """The checks and readbacks that read a product the stopped run did not complete."""
    return (
        *(check.path for check in spec.checks if _expectation_products(spec, check.expectation) & not_run),
        *(readback.path for readback in spec.readbacks if {readback.producer, readback.consumer} & not_run),
    )


def _not_evaluated_diagnostic(not_run: set[str], skipped: tuple[tuple[str | int, ...], ...]) -> Diagnostic:
    return Diagnostic(
        code=AuthoringSystemDiagnosticCode.NOT_EXECUTED,
        phase=DiagnosticPhase.EVIDENCE,
        # True also when a completed product holds a value Build cannot capture: Build then keeps no product.
        message=f"The run stopped at a failed <assert>. Build kept no capture of these products: "
        f"{', '.join(sorted(not_run))}. Build did not evaluate the "
        f"{'1 check that reads' if len(skipped) == 1 else f'{len(skipped)} checks that read'} them.",
        path=("evidence",),
        expected=[list(path) for path in skipped],
        remediation="Fix the failed <assert> and every other error of this Build. Build evaluates these checks when "
        "it captures every product.",
    )


@dataclass(frozen=True)
class AcceptanceEvaluation:
    diagnostics: tuple[Diagnostic, ...]
    # One result for each of spec.checks, in order. A path names no check: derived checks share their model path.
    results: tuple[ExpectationResult, ...]


def list_expectations(spec: AcceptanceSpecV1, results: tuple[ExpectationResult, ...] | None) -> ListedExpectations:
    """The checks of the acceptance with their results; `None` when Build evaluated none of them. Above the cap,
    the list keeps the failed checks first, then the declared ones, then the derived ones, in Build's order."""
    outcomes = (ExpectationResult.NOT_EVALUATED,) * len(spec.checks) if results is None else results
    entries = list(enumerate(zip(spec.checks, outcomes, strict=False)))
    if len(entries) > MAX_LISTED_EXPECTATIONS:
        # A reader of a rejected Build must see the failure, whatever its place in the check order.
        by_importance = sorted(
            entries,
            key=lambda entry: (
                entry[1][1] is not ExpectationResult.FAILED,
                entry[1][0].origin is AcceptanceOrigin.DERIVED,
                entry[0],
            ),
        )
        entries = sorted(by_importance[:MAX_LISTED_EXPECTATIONS], key=lambda entry: entry[0])
    listed = tuple(
        ListedExpectation(
            origin=check.origin,
            kind=check.expectation.kind,
            subject=expectation_subjects(check.expectation)[0],
            field=expectation_field(check.expectation),
            result=result,
        )
        for _, (check, result) in entries
    )
    return ListedExpectations(total=len(spec.checks), truncated=len(spec.checks) > len(listed), items=listed)


def evaluate_acceptance(
    spec: AcceptanceSpecV1, captured: CapturedProducts, *, stopped: bool = False
) -> tuple[Diagnostic, ...]:
    return evaluate_acceptance_with_results(spec, captured, stopped=stopped).diagnostics


def evaluate_acceptance_with_results(
    spec: AcceptanceSpecV1, captured: CapturedProducts, *, stopped: bool = False
) -> AcceptanceEvaluation:
    """Reject incomplete evidence before evaluating any declared or derived check. A run ``stopped`` by a failed
    <assert> captured only the products that completed before it: Build evaluates the checks on those and names the
    checks it could not evaluate."""
    unevaluated = (ExpectationResult.NOT_EVALUATED,) * len(spec.checks)
    diagnostics: list[Diagnostic] = []
    not_run: set[str] = set()
    names = [product.name for product in captured.products]
    if len(names) != len(set(names)):
        return AcceptanceEvaluation(
            (_capture_failure("Duplicate capture product identities.", ("evidence",)),), unevaluated
        )
    unknown = set(names) - {product.capture_name for product in spec.products}
    if unknown:
        return AcceptanceEvaluation(
            (_capture_failure("Capture contains undeclared product identities.", ("evidence",)),), unevaluated
        )
    if type(captured.max_count) is not int or captured.max_count < 1:
        return AcceptanceEvaluation((_capture_failure("Capture bound is invalid.", ("evidence",)),), unevaluated)
    rows_by_name: dict[str, tuple[Mapping[str, object], ...]] = {}
    retry_counts: dict[str, int] = {}
    for product in spec.products:
        item = captured.get(product.capture_name)
        path = ("evidence", product.name)
        if item is None:
            if stopped:
                not_run.add(product.name)
            else:
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
                update: dict[str, object] = {
                    "actual": {
                        "status": evidence.status.value,
                        "requested": evidence.requested,
                        "observed": evidence.observed,
                        "limit": evidence.limit,
                    }
                }
                # Only a consistent incomplete capture has a cause to name; malformed evidence keeps the
                # provenance message instead of contradicting itself ("capture is complete: ...").
                if not evidence.complete and evidence.observed == len(item.rows):
                    update["message"] = f"Product capture is {evidence.status.value}: {evidence.reason}."
                    update["remediation"] = (
                        _retry_remediation(count)
                        if retry and count is not None
                        else _incomplete_capture_remediation(evidence.status)
                    )
                diagnostic = diagnostic.model_copy(update=update)
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
    skipped = _not_evaluated(spec, not_run)
    not_evaluated = (_not_evaluated_diagnostic(not_run, skipped),) if not_run else ()
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
        return AcceptanceEvaluation((*diagnostics, *not_evaluated), unevaluated)
    results = list(unevaluated)
    for index, check in enumerate(spec.checks):
        expectation = check.expectation
        if _expectation_products(spec, expectation) & not_run:
            continue
        unevaluable = _unevaluable_sink_subject(spec, rows_by_name, expectation)
        if unevaluable is not None:
            subject, missing = unevaluable
            diagnostics.append(_unevaluable_diagnostic(subject, missing, path=check.path))
            continue
        failure = _check_expectation(spec, rows_by_name, expectation)
        if failure is None:
            results[index] = ExpectationResult.PASSED
        else:
            results[index] = ExpectationResult.FAILED
            diagnostics.append(_diagnostic(expectation.kind, failure, path=check.path))
    for readback in spec.readbacks:
        if {readback.producer, readback.consumer} & not_run:
            continue
        producer = _readback_identities(
            rows_by_name[readback.producer], tuple(join.parent_field for join in readback.joins)
        )
        consumer = _readback_identities(
            rows_by_name[readback.consumer], tuple(join.child_field for join in readback.joins)
        )
        if producer is None or consumer is None or producer != consumer:
            diagnostics.append(
                catalog_diagnostic(
                    AuthoringRuleId.VALIDATION,
                    "Memstore readback must preserve every producer identity exactly once.",
                    phase=DiagnosticPhase.EVIDENCE,
                    path=readback.path,
                    remediation=MEMSTORE_READBACK_ONCE,
                )
            )
    return AcceptanceEvaluation((*diagnostics, *not_evaluated), tuple(results))


__all__ = ["AcceptanceEvaluation", "evaluate_acceptance", "evaluate_acceptance_with_results", "list_expectations"]
