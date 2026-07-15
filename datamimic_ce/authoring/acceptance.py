# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Pure acceptance evaluation over compiler facts and one bounded capture.

This module deliberately knows neither XML nor transports.  It merges compiler-
derived and author-explicit expectations, then evaluates both against the exact
rows retained by the dry-run.  A missing or ambiguous fact is UNEVALUABLE; it is
never guessed from field names, sample rows, or global count arithmetic.
"""

from __future__ import annotations

import ast
import math
import operator
from collections.abc import Mapping
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import Literal, TypeAlias

from datamimic_ce.authoring.contracts import (
    AcceptanceReport,
    AcceptanceResult,
    AcceptanceSource,
    AcceptanceStatus,
    AllowedValuesAcceptancePlan,
    AllowedValuesAcceptanceResult,
    CaptureCompletenessEvidence,
    CaptureCompletenessStatus,
    CaptureStatus,
    CompilePlan,
    ExactCountAcceptancePlan,
    ExactCountAcceptanceResult,
    ForeignKeyAcceptancePlan,
    ForeignKeyAcceptanceResult,
    ForeignKeyRolePlan,
    GeneratedProductCompilePlan,
    IdentifierRolePlan,
    MemstoreCompletenessAcceptanceResult,
    MemstoreRelationshipPlan,
    PerParentCountAcceptancePlan,
    PerParentCountAcceptanceResult,
    ProductCaptureCompleteness,
    ProductCompilePlan,
    RangeAcceptancePlan,
    RangeAcceptanceResult,
    RequiredConsumerForeignKey,
    RowConditionAcceptanceResult,
    UniqueAcceptancePlan,
    UniqueAcceptanceResult,
)
from datamimic_ce.authoring.dryrun import CapturedProduct, CapturedProducts
from datamimic_ce.authoring.spec import (
    AllowedValuesExpectation,
    AuthoringSpecV1,
    ExactCountExpectation,
    ForeignKeyExpectation,
    PerParentCountExpectation,
    RangeExpectation,
    RowConditionExpectation,
    UniqueExpectation,
)

_BOOLEAN_OPERANDS_ERROR = "boolean operators require boolean operands"


@dataclass(frozen=True)
class _Exact:
    product: str
    count: int


@dataclass(frozen=True)
class _PerParent:
    product: str
    parent_product: str
    count: int


@dataclass(frozen=True)
class _Unique:
    product: str
    field: str
    scope: Literal["global", "per_parent"]


@dataclass(frozen=True)
class _ForeignKey:
    product: str
    child_field: str
    parent_product: str
    parent_field: str


@dataclass(frozen=True)
class _AllowedValues:
    product: str
    field: str
    values: tuple[str, ...]


@dataclass(frozen=True)
class _Range:
    product: str
    field: str
    minimum: Decimal
    maximum: Decimal


@dataclass(frozen=True)
class _RowCondition:
    product: str
    condition: str


@dataclass(frozen=True)
class _MemstoreCompleteness:
    producer_product: str
    consumer_product: str
    source_id: str


_Expectation: TypeAlias = (
    _Exact | _PerParent | _Unique | _ForeignKey | _AllowedValues | _Range | _RowCondition | _MemstoreCompleteness
)


@dataclass(frozen=True)
class _ExpectationEntry:
    expectation: _Expectation
    source: AcceptanceSource


def _derived_expectations(plan: CompilePlan) -> list[_Expectation]:
    result: list[_Expectation] = []
    for expectation in plan.derived_acceptance:
        if isinstance(expectation, ExactCountAcceptancePlan):
            result.append(_Exact(expectation.product, expectation.exact_count))
        elif isinstance(expectation, PerParentCountAcceptancePlan):
            result.append(
                _PerParent(
                    expectation.product,
                    expectation.parent_product,
                    expectation.count_per_parent,
                )
            )
        elif isinstance(expectation, UniqueAcceptancePlan):
            result.append(_Unique(expectation.product, expectation.field, expectation.scope))
        elif isinstance(expectation, ForeignKeyAcceptancePlan):
            result.append(
                _ForeignKey(
                    expectation.product,
                    expectation.child_field,
                    expectation.parent_product,
                    expectation.parent_field,
                )
            )
        elif isinstance(expectation, AllowedValuesAcceptancePlan):
            result.append(
                _AllowedValues(
                    expectation.product,
                    expectation.field,
                    tuple(expectation.allowed_values),
                )
            )
        elif isinstance(expectation, RangeAcceptancePlan):
            result.append(
                _Range(
                    expectation.product,
                    expectation.field,
                    Decimal(expectation.minimum),
                    Decimal(expectation.maximum),
                )
            )
    for relationship in plan.relationships:
        if isinstance(relationship, MemstoreRelationshipPlan):
            result.append(
                _MemstoreCompleteness(
                    relationship.parent,
                    relationship.child,
                    relationship.source_id,
                )
            )
    return result


def _explicit_expectations(spec: AuthoringSpecV1) -> list[_Expectation]:
    result: list[_Expectation] = []
    for expectation in spec.expectations:
        if isinstance(expectation, ExactCountExpectation):
            result.append(_Exact(expectation.product, expectation.count))
        elif isinstance(expectation, PerParentCountExpectation):
            result.append(
                _PerParent(
                    expectation.child_product,
                    expectation.parent_product,
                    expectation.count,
                )
            )
        elif isinstance(expectation, UniqueExpectation):
            result.append(_Unique(expectation.product, expectation.field, expectation.scope))
        elif isinstance(expectation, ForeignKeyExpectation):
            result.append(
                _ForeignKey(
                    expectation.child_product,
                    expectation.child_field,
                    expectation.parent_product,
                    expectation.parent_field,
                )
            )
        elif isinstance(expectation, AllowedValuesExpectation):
            result.append(_AllowedValues(expectation.product, expectation.field, expectation.values))
        elif isinstance(expectation, RangeExpectation):
            result.append(
                _Range(
                    expectation.product,
                    expectation.field,
                    expectation.minimum,
                    expectation.maximum,
                )
            )
        elif isinstance(expectation, RowConditionExpectation):
            result.append(_RowCondition(expectation.product, expectation.condition))
    return result


def merge_expectations(plan: CompilePlan, spec: AuthoringSpecV1) -> tuple[_ExpectationEntry, ...]:
    """Merge exact duplicates while retaining contradictory explicit assertions.

    An explicit expectation identical to a derived invariant is represented once
    with ``derived_and_explicit`` provenance.  Expectations with the same subject
    but different expected values are both retained, so a contradiction cannot be
    silently resolved in favour of either owner.
    """

    entries: list[_ExpectationEntry] = []
    positions: dict[_Expectation, int] = {}
    for expectation in _derived_expectations(plan):
        positions[expectation] = len(entries)
        entries.append(_ExpectationEntry(expectation, AcceptanceSource.DERIVED))
    for expectation in _explicit_expectations(spec):
        position = positions.get(expectation)
        if position is None:
            positions[expectation] = len(entries)
            entries.append(_ExpectationEntry(expectation, AcceptanceSource.EXPLICIT))
        elif entries[position].source is AcceptanceSource.DERIVED:
            entries[position] = replace(
                entries[position],
                source=AcceptanceSource.DERIVED_AND_EXPLICIT,
            )
    return tuple(entries)


def _rows(
    captured: CapturedProducts,
    product: str,
) -> tuple[tuple[Mapping[str, object], ...] | None, str | None]:
    capture = captured.get(product)
    if capture is None:
        return None, f"captured product '{product}' is missing"
    rows: list[Mapping[str, object]] = []
    for index, row in enumerate(capture.rows):
        if not isinstance(row, Mapping):
            return None, f"captured row {index} of '{product}' is not an object"
        rows.append(row)
    return tuple(rows), None


def _values(
    rows: tuple[Mapping[str, object], ...],
    *,
    product: str,
    field: str,
) -> tuple[list[object] | None, str | None]:
    missing = [index for index, row in enumerate(rows) if field not in row]
    if missing:
        return None, f"field '{product}.{field}' is missing in captured rows {missing[:10]}"
    return [row[field] for row in rows], None


def _display(value: object) -> str:
    return f"{type(value).__name__}:{value!r}"


def _duplicates(values: list[object]) -> list[str]:
    seen: dict[str, int] = {}
    labels: dict[str, str] = {}
    for value in values:
        key = _display(value)
        seen[key] = seen.get(key, 0) + 1
        labels[key] = repr(value)
    return sorted(labels[key] for key, count in seen.items() if count > 1)


def _product_capture_completeness(
    captured: CapturedProducts,
    product: str,
) -> ProductCaptureCompleteness:
    runtime_product = captured.get(product)
    if runtime_product is None:
        return ProductCaptureCompleteness(
            product=product,
            status=CaptureCompletenessStatus.UNKNOWN,
            reason="product is missing from the bounded runtime capture",
        )
    evidence = runtime_product.capture
    if evidence is None:
        return ProductCaptureCompleteness(
            product=product,
            status=CaptureCompletenessStatus.UNKNOWN,
            reason="runtime capture did not provide completeness evidence",
        )
    if evidence.status in (CaptureStatus.COMPLETE, CaptureStatus.EXHAUSTED):
        status = CaptureCompletenessStatus.COMPLETE
    elif evidence.status is CaptureStatus.CAPPED:
        status = CaptureCompletenessStatus.PARTIAL
    else:
        status = CaptureCompletenessStatus.UNKNOWN
    return ProductCaptureCompleteness(
        product=product,
        status=status,
        reason=evidence.reason,
        runtime_status=evidence.status,
        requested=evidence.requested,
        observed=evidence.observed,
        limit=evidence.limit,
    )


def _capture_completeness(
    captured: CapturedProducts,
    products: tuple[str, ...],
) -> CaptureCompletenessEvidence:
    proofs = [_product_capture_completeness(captured, product) for product in dict.fromkeys(products)]
    if any(proof.status is CaptureCompletenessStatus.PARTIAL for proof in proofs):
        status = CaptureCompletenessStatus.PARTIAL
    elif any(proof.status is CaptureCompletenessStatus.UNKNOWN for proof in proofs):
        status = CaptureCompletenessStatus.UNKNOWN
    else:
        status = CaptureCompletenessStatus.COMPLETE
    return CaptureCompletenessEvidence(status=status, products=proofs)


def _join_fields(
    plan: CompilePlan,
    *,
    child_product: str,
    parent_product: str,
) -> tuple[tuple[str, str] | None, str | None]:
    child = next((item for item in plan.products if item.name == child_product), None)
    parent = next((item for item in plan.products if item.name == parent_product), None)
    if child is None or parent is None:
        return None, "compile plan is missing the parent or child product"
    candidates = [
        (field.name, role.parent_field)
        for field in child.fields
        for role in field.roles
        if isinstance(role, ForeignKeyRolePlan) and role.parent_product == parent_product
    ]
    if len(candidates) != 1:
        return None, (
            f"per-parent evaluation requires exactly one explicit FK role from "
            f"'{child_product}' to '{parent_product}', found {len(candidates)}"
        )
    child_field, parent_field = candidates[0]
    if parent_field not in {field.name for field in parent.fields}:
        return None, f"compile plan is missing parent join field '{parent_product}.{parent_field}'"
    return (child_field, parent_field), None


def _group_by_parent(
    plan: CompilePlan,
    captured: CapturedProducts,
    *,
    child_product: str,
    parent_product: str,
) -> tuple[
    tuple[dict[str, list[Mapping[str, object]]], str, str] | None,
    str | None,
]:
    join, error = _join_fields(
        plan,
        child_product=child_product,
        parent_product=parent_product,
    )
    if join is None:
        return None, error
    child_field, parent_field = join
    child_rows, error = _rows(captured, child_product)
    if child_rows is None:
        return None, error
    parent_rows, error = _rows(captured, parent_product)
    if parent_rows is None:
        return None, error
    parent_values, error = _values(
        parent_rows,
        product=parent_product,
        field=parent_field,
    )
    if parent_values is None:
        return None, error
    if _duplicates(parent_values):
        return None, f"parent join field '{parent_product}.{parent_field}' is not unique"
    child_values, error = _values(
        child_rows,
        product=child_product,
        field=child_field,
    )
    if child_values is None:
        return None, error
    groups: dict[str, list[Mapping[str, object]]] = {_display(value): [] for value in parent_values}
    for row, value in zip(child_rows, child_values, strict=True):
        key = _display(value)
        if key not in groups:
            return None, (
                f"child join value {value!r} from '{child_product}.{child_field}' "
                f"has no captured '{parent_product}.{parent_field}' parent"
            )
        groups[key].append(row)
    return (groups, child_field, parent_field), None


def _exact_result(
    expectation: _Exact,
    source: AcceptanceSource,
    captured: CapturedProducts,
) -> ExactCountAcceptanceResult:
    product = captured.get(expectation.product)
    observed = len(product.rows) if product is not None else None
    if product is None:
        return ExactCountAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=f"captured product '{expectation.product}' is missing",
            product=expectation.product,
            expected_count=expectation.count,
            observed_count=None,
        )
    passed = observed == expectation.count
    return ExactCountAcceptanceResult(
        status=AcceptanceStatus.PASS if passed else AcceptanceStatus.FAIL,
        source=source,
        message=(
            f"observed {observed} rows as expected"
            if passed
            else f"expected {expectation.count} rows but observed {observed}"
        ),
        product=expectation.product,
        expected_count=expectation.count,
        observed_count=observed,
    )


def _per_parent_result(
    expectation: _PerParent,
    source: AcceptanceSource,
    plan: CompilePlan,
    captured: CapturedProducts,
) -> PerParentCountAcceptanceResult:
    grouped, error = _group_by_parent(
        plan,
        captured,
        child_product=expectation.product,
        parent_product=expectation.parent_product,
    )
    if grouped is None:
        return PerParentCountAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=str(error),
            product=expectation.product,
            parent_product=expectation.parent_product,
            expected_count_per_parent=expectation.count,
        )
    groups, child_field, parent_field = grouped
    observed = {key: len(rows) for key, rows in sorted(groups.items())}
    passed = all(count == expectation.count for count in observed.values())
    return PerParentCountAcceptanceResult(
        status=AcceptanceStatus.PASS if passed else AcceptanceStatus.FAIL,
        source=source,
        message=(
            f"every parent has {expectation.count} child rows"
            if passed
            else "one or more parents have the wrong child count"
        ),
        product=expectation.product,
        parent_product=expectation.parent_product,
        expected_count_per_parent=expectation.count,
        parent_field=parent_field,
        child_field=child_field,
        observed_counts=observed,
    )


def _unique_result(
    expectation: _Unique,
    source: AcceptanceSource,
    plan: CompilePlan,
    captured: CapturedProducts,
) -> UniqueAcceptanceResult:
    rows, error = _rows(captured, expectation.product)
    if rows is None:
        return UniqueAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=str(error),
            product=expectation.product,
            field=expectation.field,
            scope=expectation.scope,
            observed_count=None,
            distinct_count=None,
        )
    values, error = _values(rows, product=expectation.product, field=expectation.field)
    if values is None:
        return UniqueAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=str(error),
            product=expectation.product,
            field=expectation.field,
            scope=expectation.scope,
            observed_count=len(rows),
            distinct_count=None,
        )
    if expectation.scope == "global":
        duplicates, distinct_count = _global_unique_evidence(values)
    else:
        duplicates, distinct_count, scope_error = _per_parent_unique_evidence(expectation, plan, captured)
        if scope_error is not None:
            return _unevaluable_unique_result(expectation, source, len(rows), scope_error)
    passed = not duplicates
    return UniqueAcceptanceResult(
        status=AcceptanceStatus.PASS if passed else AcceptanceStatus.FAIL,
        source=source,
        message="all values are unique" if passed else "duplicate values were captured",
        product=expectation.product,
        field=expectation.field,
        scope=expectation.scope,
        observed_count=len(rows),
        distinct_count=distinct_count,
        duplicate_values=duplicates[:20],
    )


def _global_unique_evidence(values: list[object]) -> tuple[list[str], int]:
    return _duplicates(values), len({_display(value) for value in values})


def _per_parent_unique_evidence(
    expectation: _Unique,
    plan: CompilePlan,
    captured: CapturedProducts,
) -> tuple[list[str], int, str | None]:
    product_plan = next(
        (item for item in plan.products if item.name == expectation.product),
        None,
    )
    if not isinstance(product_plan, GeneratedProductCompilePlan) or product_plan.parent is None:
        return [], 0, "per-parent uniqueness requires a nested product in CompilePlan"
    grouped, error = _group_by_parent(
        plan,
        captured,
        child_product=expectation.product,
        parent_product=product_plan.parent,
    )
    if grouped is None:
        return [], 0, str(error)
    groups, _child_field, _parent_field = grouped
    duplicates: list[str] = []
    distinct_count = 0
    for parent, group_rows in sorted(groups.items()):
        group_values, error = _values(
            tuple(group_rows),
            product=expectation.product,
            field=expectation.field,
        )
        if group_values is None:
            return [], 0, str(error)
        duplicates.extend(f"parent={parent}:{value}" for value in _duplicates(group_values))
        distinct_count += len({_display(value) for value in group_values})
    return duplicates, distinct_count, None


def _unevaluable_unique_result(
    expectation: _Unique,
    source: AcceptanceSource,
    observed_count: int,
    message: str,
) -> UniqueAcceptanceResult:
    return UniqueAcceptanceResult(
        status=AcceptanceStatus.UNEVALUABLE,
        source=source,
        message=message,
        product=expectation.product,
        field=expectation.field,
        scope=expectation.scope,
        observed_count=observed_count,
        distinct_count=None,
    )


def _foreign_key_result(
    expectation: _ForeignKey,
    source: AcceptanceSource,
    captured: CapturedProducts,
) -> ForeignKeyAcceptanceResult:
    child_rows, error = _rows(captured, expectation.product)
    if child_rows is None:
        return ForeignKeyAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=str(error),
            product=expectation.product,
            child_field=expectation.child_field,
            parent_product=expectation.parent_product,
            parent_field=expectation.parent_field,
            observed_count=None,
        )
    parent_rows, error = _rows(captured, expectation.parent_product)
    if parent_rows is None:
        return ForeignKeyAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=str(error),
            product=expectation.product,
            child_field=expectation.child_field,
            parent_product=expectation.parent_product,
            parent_field=expectation.parent_field,
            observed_count=len(child_rows),
        )
    child_values, error = _values(
        child_rows,
        product=expectation.product,
        field=expectation.child_field,
    )
    if child_values is None:
        status_error = error
    else:
        parent_values, status_error = _values(
            parent_rows,
            product=expectation.parent_product,
            field=expectation.parent_field,
        )
        if parent_values is not None:
            parent_keys = {_display(value) for value in parent_values}
            missing = sorted({repr(value) for value in child_values if _display(value) not in parent_keys})
            return ForeignKeyAcceptanceResult(
                status=AcceptanceStatus.PASS if not missing else AcceptanceStatus.FAIL,
                source=source,
                message=(
                    "all foreign keys reference a captured parent"
                    if not missing
                    else "one or more foreign keys have no captured parent"
                ),
                product=expectation.product,
                child_field=expectation.child_field,
                parent_product=expectation.parent_product,
                parent_field=expectation.parent_field,
                observed_count=len(child_values),
                missing_values=missing[:20],
            )
    return ForeignKeyAcceptanceResult(
        status=AcceptanceStatus.UNEVALUABLE,
        source=source,
        message=str(status_error),
        product=expectation.product,
        child_field=expectation.child_field,
        parent_product=expectation.parent_product,
        parent_field=expectation.parent_field,
        observed_count=len(child_rows),
    )


def _allowed_values_result(
    expectation: _AllowedValues,
    source: AcceptanceSource,
    captured: CapturedProducts,
) -> AllowedValuesAcceptanceResult:
    rows, error = _rows(captured, expectation.product)
    values = (
        None
        if rows is None
        else _values(
            rows,
            product=expectation.product,
            field=expectation.field,
        )[0]
    )
    if rows is None or values is None:
        if rows is not None:
            _ignored, error = _values(
                rows,
                product=expectation.product,
                field=expectation.field,
            )
        return AllowedValuesAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=str(error),
            product=expectation.product,
            field=expectation.field,
            allowed_values=list(expectation.values),
            observed_count=None if rows is None else len(rows),
        )
    allowed = set(expectation.values)
    unexpected = sorted({repr(value) for value in values if not isinstance(value, str) or value not in allowed})
    return AllowedValuesAcceptanceResult(
        status=AcceptanceStatus.PASS if not unexpected else AcceptanceStatus.FAIL,
        source=source,
        message="all values are allowed" if not unexpected else "unexpected values were captured",
        product=expectation.product,
        field=expectation.field,
        allowed_values=list(expectation.values),
        observed_count=len(values),
        unexpected_values=unexpected[:20],
    )


def _range_result(
    expectation: _Range,
    source: AcceptanceSource,
    captured: CapturedProducts,
) -> RangeAcceptanceResult:
    rows, error = _rows(captured, expectation.product)
    values = (
        None
        if rows is None
        else _values(
            rows,
            product=expectation.product,
            field=expectation.field,
        )[0]
    )
    if rows is None or values is None:
        if rows is not None:
            _ignored, error = _values(
                rows,
                product=expectation.product,
                field=expectation.field,
            )
        return RangeAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=str(error),
            product=expectation.product,
            field=expectation.field,
            expected_minimum=str(expectation.minimum),
            expected_maximum=str(expectation.maximum),
        )
    decimals: list[Decimal] = []
    try:
        for value in values:
            decimal_value = Decimal(str(value))
            if not decimal_value.is_finite():
                raise InvalidOperation
            decimals.append(decimal_value)
    except (InvalidOperation, ValueError):
        return RangeAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=f"field '{expectation.product}.{expectation.field}' contains a non-numeric value",
            product=expectation.product,
            field=expectation.field,
            expected_minimum=str(expectation.minimum),
            expected_maximum=str(expectation.maximum),
        )
    violations = [
        index for index, value in enumerate(decimals) if value < expectation.minimum or value > expectation.maximum
    ]
    return RangeAcceptanceResult(
        status=AcceptanceStatus.PASS if not violations else AcceptanceStatus.FAIL,
        source=source,
        message="all values are within range" if not violations else "out-of-range values were captured",
        product=expectation.product,
        field=expectation.field,
        expected_minimum=str(expectation.minimum),
        expected_maximum=str(expectation.maximum),
        observed_minimum=str(min(decimals)) if decimals else None,
        observed_maximum=str(max(decimals)) if decimals else None,
        violating_rows=violations[:20],
    )


_BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}
_COMPARE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
}

_MAX_CONDITION_LENGTH = 4096
_MAX_CONDITION_NODES = 96
_MAX_CONDITION_DEPTH = 12
_MAX_LITERAL_LENGTH = 1024
_MAX_CONTAINER_ITEMS = 64
_MAX_INTEGER_BITS = 256
_MAX_DECIMAL_MAGNITUDE = 128
_MAX_FLOAT_MAGNITUDE = 1e100


class _UnsafeCondition(ValueError):
    pass


def _safe_number(value: object) -> int | float | Decimal:
    if isinstance(value, bool):
        raise _UnsafeCondition("boolean values are not numeric condition operands")
    if isinstance(value, int):
        if value.bit_length() > _MAX_INTEGER_BITS:
            raise _UnsafeCondition("integer operand exceeds the numeric budget")
        return value
    if isinstance(value, float):
        if not math.isfinite(value) or abs(value) > _MAX_FLOAT_MAGNITUDE:
            raise _UnsafeCondition("float operand exceeds the finite numeric budget")
        return value
    if isinstance(value, Decimal):
        if not value.is_finite() or abs(value.adjusted()) > _MAX_DECIMAL_MAGNITUDE:
            raise _UnsafeCondition("decimal operand exceeds the finite numeric budget")
        return value
    raise _UnsafeCondition("arithmetic accepts only bounded numeric operands")


def _safe_condition_value(value: object) -> object:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int | float | Decimal):
        return _safe_number(value)
    if isinstance(value, str):
        if len(value) > _MAX_LITERAL_LENGTH:
            raise _UnsafeCondition("string operand exceeds the literal budget")
        return value
    if isinstance(value, list | tuple | set):
        if len(value) > _MAX_CONTAINER_ITEMS:
            raise _UnsafeCondition("container operand exceeds the item budget")
        for item in value:
            if isinstance(item, list | tuple | set | dict):
                raise _UnsafeCondition("nested containers are not supported in conditions")
            _safe_condition_value(item)
        return value
    raise _UnsafeCondition(f"unsupported operand type '{type(value).__name__}' in row condition")


def _validate_condition_tree(tree: ast.AST) -> None:
    _ConditionTreeValidator().validate(tree)


class _ConditionTreeValidator:
    """Validate one typed condition AST against the bounded expression contract."""

    def __init__(self) -> None:
        self._node_count = 0

    def validate(self, tree: ast.AST) -> None:
        self._visit(tree, 0)

    def _visit(self, node: ast.AST, depth: int) -> None:
        self._node_count += 1
        if self._node_count > _MAX_CONDITION_NODES:
            raise _UnsafeCondition("condition exceeds the AST node budget")
        if depth > _MAX_CONDITION_DEPTH:
            raise _UnsafeCondition("condition exceeds the AST depth budget")
        self._validate_node(node)
        for child in ast.iter_child_nodes(node):
            self._visit(child, depth + 1)

    @staticmethod
    def _validate_node(node: ast.AST) -> None:
        if isinstance(node, ast.Constant):
            _safe_condition_value(node.value)
        if isinstance(node, ast.List | ast.Tuple | ast.Set) and len(node.elts) > _MAX_CONTAINER_ITEMS:
            raise _UnsafeCondition("condition literal exceeds the container budget")
        if isinstance(node, ast.BinOp):
            _ConditionTreeValidator._validate_repetition(node)

    @staticmethod
    def _validate_repetition(node: ast.BinOp) -> None:
        if not isinstance(node.op, ast.Mult):
            return
        if isinstance(node.left, ast.List | ast.Tuple | ast.Set) or isinstance(
            node.right,
            ast.List | ast.Tuple | ast.Set,
        ):
            raise _UnsafeCondition("sequence repetition is forbidden in row conditions")
        if (isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)) or (
            isinstance(node.right, ast.Constant) and isinstance(node.right.value, str)
        ):
            raise _UnsafeCondition("string repetition is forbidden in row conditions")


def _eval_condition_node(node: ast.AST, row: Mapping[str, object]) -> object:
    return _ConditionEvaluator(row).evaluate(node)


class _ConditionEvaluator:
    """Evaluate the explicitly supported condition AST without dynamic dispatch."""

    def __init__(self, row: Mapping[str, object]) -> None:
        self._row = row

    def evaluate(self, node: ast.AST) -> object:
        if isinstance(node, ast.Expression):
            return self.evaluate(node.body)
        if isinstance(node, ast.Constant):
            return _safe_condition_value(node.value)
        if isinstance(node, ast.Name):
            return self._name(node)
        if isinstance(node, ast.List):
            return [self.evaluate(item) for item in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self.evaluate(item) for item in node.elts)
        if isinstance(node, ast.Set):
            return {self.evaluate(item) for item in node.elts}
        if isinstance(node, ast.UnaryOp):
            return self._unary(node)
        if isinstance(node, ast.BinOp):
            return self._binary(node)
        if isinstance(node, ast.BoolOp):
            return self._boolean(node)
        if isinstance(node, ast.Compare):
            return self._compare(node)
        raise _UnsafeCondition(
            f"unsupported condition syntax '{type(node).__name__}'; calls, attributes, and subscripts are forbidden"
        )

    def _name(self, node: ast.Name) -> object:
        if node.id not in self._row:
            raise _UnsafeCondition(f"name '{node.id}' is missing from the captured row")
        return _safe_condition_value(self._row[node.id])

    def _unary(self, node: ast.UnaryOp) -> object:
        operand = self.evaluate(node.operand)
        if isinstance(node.op, ast.Not):
            if not isinstance(operand, bool):
                raise _UnsafeCondition("not requires a boolean operand")
            return not operand
        if isinstance(node.op, ast.USub):
            return _safe_number(-_safe_number(operand))
        if isinstance(node.op, ast.UAdd):
            return _safe_number(+_safe_number(operand))
        raise _UnsafeCondition("unsupported unary operator")

    def _binary(self, node: ast.BinOp) -> object:
        operation = _BINARY_OPERATORS.get(type(node.op))
        if operation is None:
            raise _UnsafeCondition("unsupported binary operator")
        left = _safe_number(self.evaluate(node.left))
        right = _safe_number(self.evaluate(node.right))
        return _safe_number(operation(left, right))

    def _boolean(self, node: ast.BoolOp) -> bool:
        bool_result = self.evaluate(node.values[0])
        if not isinstance(bool_result, bool):
            raise _UnsafeCondition(_BOOLEAN_OPERANDS_ERROR)
        if isinstance(node.op, ast.And):
            return self._and(node.values[1:], bool_result)
        if isinstance(node.op, ast.Or):
            return self._or(node.values[1:], bool_result)
        raise _UnsafeCondition("unsupported boolean operator")

    def _and(self, values: list[ast.expr], result: bool) -> bool:
        for value in values:
            if not result:
                return result
            next_result = self.evaluate(value)
            if not isinstance(next_result, bool):
                raise _UnsafeCondition(_BOOLEAN_OPERANDS_ERROR)
            result = next_result
        return result

    def _or(self, values: list[ast.expr], result: bool) -> bool:
        for value in values:
            if result:
                return result
            next_result = self.evaluate(value)
            if not isinstance(next_result, bool):
                raise _UnsafeCondition(_BOOLEAN_OPERANDS_ERROR)
            result = next_result
        return result

    def _compare(self, node: ast.Compare) -> bool:
        compare_left = self.evaluate(node.left)
        for operation_node, comparator in zip(node.ops, node.comparators, strict=True):
            operation = _COMPARE_OPERATORS.get(type(operation_node))
            if operation is None:
                raise _UnsafeCondition("unsupported comparison operator")
            compare_right = self.evaluate(comparator)
            _safe_condition_value(compare_left)
            _safe_condition_value(compare_right)
            if isinstance(operation_node, ast.In | ast.NotIn) and not isinstance(
                compare_right,
                list | tuple | set,
            ):
                raise _UnsafeCondition("membership requires a bounded container")
            if not operation(compare_left, compare_right):
                return False
            compare_left = compare_right
        return True


def _row_condition_result(
    expectation: _RowCondition,
    source: AcceptanceSource,
    captured: CapturedProducts,
) -> RowConditionAcceptanceResult:
    rows, error = _rows(captured, expectation.product)
    if rows is None:
        return RowConditionAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=str(error),
            product=expectation.product,
            condition=expectation.condition,
            observed_count=None,
        )
    if len(expectation.condition) > _MAX_CONDITION_LENGTH:
        return RowConditionAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message="condition exceeds the expression length budget",
            product=expectation.product,
            condition=expectation.condition,
            observed_count=len(rows),
            evaluation_errors=["expression length budget exceeded"],
        )
    try:
        tree = ast.parse(expectation.condition, mode="eval")
    except SyntaxError as syntax_error:
        return RowConditionAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=f"condition syntax is invalid: {syntax_error.msg}",
            product=expectation.product,
            condition=expectation.condition,
            observed_count=len(rows),
            evaluation_errors=[syntax_error.msg],
        )
    try:
        _validate_condition_tree(tree)
    except _UnsafeCondition as validation_error:
        return RowConditionAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message="condition exceeds the safe typed expression contract",
            product=expectation.product,
            condition=expectation.condition,
            observed_count=len(rows),
            evaluation_errors=[str(validation_error)],
        )
    failed: list[int] = []
    errors: list[str] = []
    for index, row in enumerate(rows):
        try:
            result = _eval_condition_node(tree, row)
            if type(result) is not bool:
                raise _UnsafeCondition("condition result is not bool")
            if not result:
                failed.append(index)
        except (ArithmeticError, TypeError, ValueError) as evaluation_error:
            errors.append(f"row {index}: {evaluation_error}")
    if errors:
        return RowConditionAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message="condition could not be safely evaluated for every row",
            product=expectation.product,
            condition=expectation.condition,
            observed_count=len(rows),
            failed_rows=failed[:20],
            evaluation_errors=errors[:20],
        )
    return RowConditionAcceptanceResult(
        status=AcceptanceStatus.PASS if not failed else AcceptanceStatus.FAIL,
        source=source,
        message="condition holds for every row" if not failed else "condition failed for captured rows",
        product=expectation.product,
        condition=expectation.condition,
        observed_count=len(rows),
        failed_rows=failed[:20],
    )


def _memstore_result(
    expectation: _MemstoreCompleteness,
    source: AcceptanceSource,
    plan: CompilePlan,
    captured: CapturedProducts,
) -> MemstoreCompletenessAcceptanceResult:
    resolved_context = _resolve_memstore_context(expectation, source, plan, captured)
    if isinstance(resolved_context, MemstoreCompletenessAcceptanceResult):
        return resolved_context
    count_result = _memstore_count_result(resolved_context)
    if count_result is not None:
        return count_result
    resolved_binding = _resolve_memstore_binding(resolved_context)
    if isinstance(resolved_binding, MemstoreCompletenessAcceptanceResult):
        return resolved_binding
    resolved_values = _resolve_memstore_values(resolved_context, resolved_binding, captured)
    if isinstance(resolved_values, MemstoreCompletenessAcceptanceResult):
        return resolved_values
    return _memstore_identity_result(resolved_context, resolved_binding, resolved_values)


@dataclass(frozen=True)
class _MemstoreContext:
    expectation: _MemstoreCompleteness
    source: AcceptanceSource
    producer: CapturedProduct
    consumer: CapturedProduct
    consumer_plan: ProductCompilePlan
    producer_identifiers: frozenset[str]
    required_foreign_key: RequiredConsumerForeignKey | None


@dataclass(frozen=True)
class _MemstoreBinding:
    consumer_key_field: str
    producer_key_field: str


@dataclass(frozen=True)
class _MemstoreValues:
    producer: list[object]
    consumer: list[object]


def _resolve_memstore_context(
    expectation: _MemstoreCompleteness,
    source: AcceptanceSource,
    plan: CompilePlan,
    captured: CapturedProducts,
) -> _MemstoreContext | MemstoreCompletenessAcceptanceResult:
    producer = captured.get(expectation.producer_product)
    consumer = captured.get(expectation.consumer_product)
    if producer is None or consumer is None:
        missing_product = expectation.producer_product if producer is None else expectation.consumer_product
        return MemstoreCompletenessAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message=f"captured product '{missing_product}' is missing",
            producer_product=expectation.producer_product,
            consumer_product=expectation.consumer_product,
            source_id=expectation.source_id,
            producer_count=None if producer is None else len(producer.rows),
            consumer_count=None if consumer is None else len(consumer.rows),
        )

    producer_plan = next(
        (item for item in plan.products if item.name == expectation.producer_product),
        None,
    )
    consumer_plan = next(
        (item for item in plan.products if item.name == expectation.consumer_product),
        None,
    )
    if producer_plan is None or consumer_plan is None:
        return MemstoreCompletenessAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=source,
            message="compile plan is missing the producer or consumer product",
            producer_product=expectation.producer_product,
            consumer_product=expectation.consumer_product,
            source_id=expectation.source_id,
            producer_count=len(producer.rows),
            consumer_count=len(consumer.rows),
        )
    producer_identifiers = frozenset(
        field.name
        for field in producer_plan.fields
        if any(isinstance(role, IdentifierRolePlan) for role in field.roles)
    )
    required_foreign_key = _required_memstore_foreign_key(
        expectation,
        consumer_plan,
        producer_identifiers,
    )
    return _MemstoreContext(
        expectation=expectation,
        source=source,
        producer=producer,
        consumer=consumer,
        consumer_plan=consumer_plan,
        producer_identifiers=producer_identifiers,
        required_foreign_key=required_foreign_key,
    )


def _required_memstore_foreign_key(
    expectation: _MemstoreCompleteness,
    consumer_plan: ProductCompilePlan,
    producer_identifiers: frozenset[str],
) -> RequiredConsumerForeignKey | None:
    if len(producer_identifiers) != 1:
        return None
    producer_identifier = next(iter(producer_identifiers))
    observed_roles = sum(
        1
        for field in consumer_plan.fields
        for role in field.roles
        if isinstance(role, ForeignKeyRolePlan)
        and role.parent_product == expectation.producer_product
        and role.parent_field == producer_identifier
    )
    return RequiredConsumerForeignKey(
        parent_product=expectation.producer_product,
        parent_field=producer_identifier,
        observed_count=observed_roles,
    )


def _memstore_count_result(
    context: _MemstoreContext,
) -> MemstoreCompletenessAcceptanceResult | None:
    if len(context.producer.rows) != len(context.consumer.rows):
        return MemstoreCompletenessAcceptanceResult(
            status=AcceptanceStatus.FAIL,
            source=context.source,
            message="producer and memstore consumer bounded row counts differ",
            producer_product=context.expectation.producer_product,
            consumer_product=context.expectation.consumer_product,
            source_id=context.expectation.source_id,
            producer_count=len(context.producer.rows),
            consumer_count=len(context.consumer.rows),
            required_consumer_foreign_key=context.required_foreign_key,
        )
    return None


def _resolve_memstore_binding(
    context: _MemstoreContext,
) -> _MemstoreBinding | MemstoreCompletenessAcceptanceResult:
    candidates = [
        (field.name, role.parent_field)
        for field in context.consumer_plan.fields
        for role in field.roles
        if isinstance(role, ForeignKeyRolePlan)
        and role.parent_product == context.expectation.producer_product
        and role.parent_field in context.producer_identifiers
    ]
    if len(candidates) != 1:
        return MemstoreCompletenessAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=context.source,
            message=(
                "memstore completeness requires exactly one explicit consumer FK role "
                "targeting a typed producer identifier; "
                f"found {len(candidates)}"
            ),
            producer_product=context.expectation.producer_product,
            consumer_product=context.expectation.consumer_product,
            source_id=context.expectation.source_id,
            producer_count=len(context.producer.rows),
            consumer_count=len(context.consumer.rows),
            required_consumer_foreign_key=context.required_foreign_key,
        )
    consumer_key_field, producer_key_field = candidates[0]
    return _MemstoreBinding(
        consumer_key_field=consumer_key_field,
        producer_key_field=producer_key_field,
    )


def _resolve_memstore_values(
    context: _MemstoreContext,
    binding: _MemstoreBinding,
    captured: CapturedProducts,
) -> _MemstoreValues | MemstoreCompletenessAcceptanceResult:
    producer_rows, producer_error = _rows(
        captured,
        context.expectation.producer_product,
    )
    consumer_rows, consumer_error = _rows(
        captured,
        context.expectation.consumer_product,
    )
    if producer_rows is None or consumer_rows is None:
        return _unevaluable_memstore_values(
            context,
            binding,
            str(producer_error or consumer_error),
        )
    producer_values, producer_error = _values(
        producer_rows,
        product=context.expectation.producer_product,
        field=binding.producer_key_field,
    )
    consumer_values, consumer_error = _values(
        consumer_rows,
        product=context.expectation.consumer_product,
        field=binding.consumer_key_field,
    )
    if producer_values is None or consumer_values is None:
        return _unevaluable_memstore_values(
            context,
            binding,
            str(producer_error or consumer_error),
        )
    return _MemstoreValues(producer=producer_values, consumer=consumer_values)


def _unevaluable_memstore_values(
    context: _MemstoreContext,
    binding: _MemstoreBinding,
    message: str,
) -> MemstoreCompletenessAcceptanceResult:
    return MemstoreCompletenessAcceptanceResult(
        status=AcceptanceStatus.UNEVALUABLE,
        source=context.source,
        message=message,
        producer_product=context.expectation.producer_product,
        consumer_product=context.expectation.consumer_product,
        source_id=context.expectation.source_id,
        producer_count=len(context.producer.rows),
        consumer_count=len(context.consumer.rows),
        producer_key_field=binding.producer_key_field,
        consumer_key_field=binding.consumer_key_field,
        required_consumer_foreign_key=context.required_foreign_key,
    )


def _memstore_identity_result(
    context: _MemstoreContext,
    binding: _MemstoreBinding,
    values: _MemstoreValues,
) -> MemstoreCompletenessAcceptanceResult:
    producer_keys = {_display(value) for value in values.producer}
    consumer_keys = {_display(value) for value in values.consumer}
    producer_labels = {_display(value): repr(value) for value in values.producer}
    consumer_labels = {_display(value): repr(value) for value in values.consumer}
    missing = sorted(producer_labels[key] for key in producer_keys - consumer_keys)
    unexpected = sorted(consumer_labels[key] for key in consumer_keys - producer_keys)
    duplicate_producer = _duplicates(values.producer)
    duplicate_consumer = _duplicates(values.consumer)
    passed = not (missing or unexpected or duplicate_producer or duplicate_consumer)
    return MemstoreCompletenessAcceptanceResult(
        status=AcceptanceStatus.PASS if passed else AcceptanceStatus.FAIL,
        source=context.source,
        message=(
            "every bounded producer identity was read back exactly once"
            if passed
            else "memstore consumer identities do not exactly match producer identities"
        ),
        producer_product=context.expectation.producer_product,
        consumer_product=context.expectation.consumer_product,
        source_id=context.expectation.source_id,
        producer_count=len(context.producer.rows),
        consumer_count=len(context.consumer.rows),
        producer_key_field=binding.producer_key_field,
        consumer_key_field=binding.consumer_key_field,
        required_consumer_foreign_key=context.required_foreign_key,
        missing_keys=missing[:20],
        unexpected_keys=unexpected[:20],
        duplicate_producer_keys=duplicate_producer[:20],
        duplicate_consumer_keys=duplicate_consumer[:20],
    )


def _expectation_products(expectation: _Expectation) -> tuple[str, ...]:
    if isinstance(expectation, _PerParent):
        return expectation.product, expectation.parent_product
    if isinstance(expectation, _ForeignKey):
        return expectation.product, expectation.parent_product
    if isinstance(expectation, _MemstoreCompleteness):
        return expectation.producer_product, expectation.consumer_product
    return (expectation.product,)


def _incomplete_message(evidence: CaptureCompletenessEvidence) -> str:
    details = "; ".join(f"{proof.product}: {proof.reason}" for proof in evidence.products)
    return f"whole-product expectation requires a complete capture; {details}"


def _incomplete_result(
    entry: _ExpectationEntry,
    captured: CapturedProducts,
    evidence: CaptureCompletenessEvidence,
) -> AcceptanceResult:
    result = _incomplete_result_without_evidence(
        entry,
        captured,
        _incomplete_message(evidence),
    )
    return result.with_capture_completeness(evidence)


def _captured_count(captured: CapturedProducts, product: str) -> int | None:
    capture = captured.get(product)
    if capture is None:
        return None
    return len(capture.rows)


def _incomplete_result_without_evidence(
    entry: _ExpectationEntry,
    captured: CapturedProducts,
    message: str,
) -> AcceptanceResult:
    expectation = entry.expectation
    if isinstance(expectation, _Exact):
        return ExactCountAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=entry.source,
            message=message,
            product=expectation.product,
            expected_count=expectation.count,
            observed_count=_captured_count(captured, expectation.product),
        )
    if isinstance(expectation, _PerParent):
        return PerParentCountAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=entry.source,
            message=message,
            product=expectation.product,
            parent_product=expectation.parent_product,
            expected_count_per_parent=expectation.count,
        )
    if isinstance(expectation, _Unique):
        return UniqueAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=entry.source,
            message=message,
            product=expectation.product,
            field=expectation.field,
            scope=expectation.scope,
            observed_count=_captured_count(captured, expectation.product),
            distinct_count=None,
        )
    if isinstance(expectation, _ForeignKey):
        return ForeignKeyAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=entry.source,
            message=message,
            product=expectation.product,
            child_field=expectation.child_field,
            parent_product=expectation.parent_product,
            parent_field=expectation.parent_field,
            observed_count=_captured_count(captured, expectation.product),
        )
    if isinstance(expectation, _AllowedValues):
        return AllowedValuesAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=entry.source,
            message=message,
            product=expectation.product,
            field=expectation.field,
            allowed_values=list(expectation.values),
            observed_count=_captured_count(captured, expectation.product),
        )
    if isinstance(expectation, _Range):
        return RangeAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=entry.source,
            message=message,
            product=expectation.product,
            field=expectation.field,
            expected_minimum=str(expectation.minimum),
            expected_maximum=str(expectation.maximum),
        )
    if isinstance(expectation, _RowCondition):
        return RowConditionAcceptanceResult(
            status=AcceptanceStatus.UNEVALUABLE,
            source=entry.source,
            message=message,
            product=expectation.product,
            condition=expectation.condition,
            observed_count=_captured_count(captured, expectation.product),
        )
    return MemstoreCompletenessAcceptanceResult(
        status=AcceptanceStatus.UNEVALUABLE,
        source=entry.source,
        message=message,
        producer_product=expectation.producer_product,
        consumer_product=expectation.consumer_product,
        source_id=expectation.source_id,
        producer_count=_captured_count(captured, expectation.producer_product),
        consumer_count=_captured_count(captured, expectation.consumer_product),
    )


def _evaluate_entry(
    entry: _ExpectationEntry,
    plan: CompilePlan,
    captured: CapturedProducts,
) -> AcceptanceResult:
    expectation = entry.expectation
    completeness = _capture_completeness(
        captured,
        _expectation_products(expectation),
    )
    if completeness.status is not CaptureCompletenessStatus.COMPLETE:
        return _incomplete_result(entry, captured, completeness)
    result: AcceptanceResult
    if isinstance(expectation, _Exact):
        result = _exact_result(expectation, entry.source, captured)
    elif isinstance(expectation, _PerParent):
        result = _per_parent_result(expectation, entry.source, plan, captured)
    elif isinstance(expectation, _Unique):
        result = _unique_result(expectation, entry.source, plan, captured)
    elif isinstance(expectation, _ForeignKey):
        result = _foreign_key_result(expectation, entry.source, captured)
    elif isinstance(expectation, _AllowedValues):
        result = _allowed_values_result(expectation, entry.source, captured)
    elif isinstance(expectation, _Range):
        result = _range_result(expectation, entry.source, captured)
    elif isinstance(expectation, _RowCondition):
        result = _row_condition_result(expectation, entry.source, captured)
    else:
        result = _memstore_result(expectation, entry.source, plan, captured)
    return result.with_capture_completeness(completeness)


def evaluate_acceptance(
    plan: CompilePlan,
    spec: AuthoringSpecV1,
    captured: CapturedProducts,
) -> AcceptanceReport:
    """Evaluate every mandatory expectation against all rows in one bounded capture."""

    results = [_evaluate_entry(entry, plan, captured) for entry in merge_expectations(plan, spec)]
    passed = sum(result.status is AcceptanceStatus.PASS for result in results)
    failed = sum(result.status is AcceptanceStatus.FAIL for result in results)
    unevaluable = sum(result.status is AcceptanceStatus.UNEVALUABLE for result in results)
    return AcceptanceReport(
        verified=bool(results) and failed == 0 and unevaluable == 0,
        passed=passed,
        failed=failed,
        unevaluable=unevaluable,
        results=results,
    )


__all__ = ["evaluate_acceptance", "merge_expectations"]
