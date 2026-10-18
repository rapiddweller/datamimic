# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""One CE capture core with bounded counts, neutralized targets and full provenance.

The bounded executor owns private workspaces, process cleanup and transport.
Smoke exporters consume the same validated full capture before projection.
"""

import io
import os
import pickle
import tempfile
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, StrictBool, StrictStr, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass

from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.capture import (
    CapturedProduct,
    CapturedProducts,
    CaptureStatus,
    ProductCaptureEvidence,
    SmokeExportCapture,
    validate_capture_values,
)
from datamimic_ce.authoring.domain.common import NonEmptyStrictStr, NonNegativeStrictInt, PositiveStrictInt
from datamimic_ce.authoring.domain.rule_catalog import RuleSeverity
from datamimic_ce.authoring.domain.xml_diagnostics import Diagnostic
from datamimic_ce.engine.dsl.api import capture_product_name, resource_reader_scope
from datamimic_ce.engine.io.contracts import SmokeExportRequest
from datamimic_ce.errors import DomainError, MissingMemstoreProductError, UserErrorBase, is_user_error
from datamimic_ce.errors.catalog import get_issue_definition
from datamimic_ce.errors.codes import IssueCode
from datamimic_ce.errors.context.descriptor_identity import descriptor_scope

RULE_RUNTIME_ERROR = "DM002"


@dataclass(frozen=True, config=ConfigDict(extra="forbid", strict=True, revalidate_instances="always"))
class _ProductBudget:
    """Static boundary facts recorded while the runtime statement tree is transformed."""

    name: NonEmptyStrictStr
    parent_name: NonEmptyStrictStr | None
    requested_per_parent: NonNegativeStrictInt | None
    explicit_count: StrictBool
    count_kind: "_CountBoundaryKind"
    source_rows_per_parent: NonNegativeStrictInt | None
    source_exhaustible: StrictBool
    memstore_source: "_MemstoreSourceBinding | None"
    source_offset: NonNegativeStrictInt
    cyclic: StrictBool
    output_multiplier: PositiveStrictInt
    bounded_without_cap: StrictBool
    cap_applied: StrictBool
    reason: NonEmptyStrictStr


_ProductBudgets = dict[str, _ProductBudget]


class _CountBoundaryKind(StrEnum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    RANGE = "range"
    SOURCE = "source"


@dataclass(frozen=True, config=ConfigDict(extra="forbid", strict=True, revalidate_instances="always"))
class _MemstoreProducer:
    """One runtime statement that writes a typed entity into a declared memstore."""

    source_id: NonEmptyStrictStr
    entity: str
    product: NonEmptyStrictStr


class _MemstoreBindingStatus(StrEnum):
    RESOLVED = "resolved"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, config=ConfigDict(extra="forbid", strict=True, revalidate_instances="always"))
class _MemstoreSourceBinding:
    """Typed runtime routing fact for one generate reading a memstore entity."""

    source_id: NonEmptyStrictStr
    entity: str | None
    status: _MemstoreBindingStatus
    producers: tuple[_MemstoreProducer, ...]


@dataclass(frozen=True, config=ConfigDict(extra="forbid", strict=True, revalidate_instances="always"))
class _WorkerSuccess:
    captured: dict[NonEmptyStrictStr, tuple[dict[StrictStr, object], ...]]
    budgets: tuple[_ProductBudget, ...]
    smoke_diagnostics: tuple[dict[str, object], ...]
    smoke_export: SmokeExportCapture


@dataclass(frozen=True, config=ConfigDict(extra="forbid", strict=True, revalidate_instances="always"))
class _WorkerFailure:
    message: NonEmptyStrictStr
    fix_hint: NonEmptyStrictStr
    error: object | None = None
    policy_refusal: StrictBool = False


class _BoundedPolicyRefusal(ValueError):
    """A parsed operation cannot inherit bounded execution guarantees."""


_WorkerMessage = _WorkerSuccess | _WorkerFailure


_SCOPE_HINT = (
    "A script may reference an unavailable name or an unexpected value structure. Check spelling, definition order,"
    " and value shape. Names in the current scope can resolve bare or via this.name; existing outermost bare names"
    " take precedence on collisions. Use parent.name for the immediate enclosing scope, root.name for an"
    " outermost field, or a qualified scope path to select the intended value. Intermediate ancestor names are"
    " not automatically available bare. CSV columns arrive as strings (cast: int(parent.col))."
)


def _runtime_hint(err: Exception) -> str:
    current: BaseException | None = err
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, MissingMemstoreProductError):
            return current.guidance
        if isinstance(current, UserErrorBase) and current.issue_code is not None:
            if current.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED:
                return _SCOPE_HINT
            issue = get_issue_definition(current.issue_code)
            return issue.guidance or issue.resolution
        if isinstance(current, DomainError) and current.hint:
            return current.hint
        if isinstance(current, FileNotFoundError):
            return "Provide the referenced resource relative to the descriptor workspace."
        current = current.__cause__
    return "Repair the reported runtime input or workspace configuration."


def _memstore_ids(root_stmt: object) -> set[str]:
    from datamimic_ce.engine.dsl.api import MemstoreStatement, SetupStatement

    assert isinstance(root_stmt, SetupStatement)
    return {stmt.id for stmt in root_stmt.sub_statements if isinstance(stmt, MemstoreStatement)}


def _generate_statements(root_stmt: object) -> tuple[object, ...]:
    """Collect generate statements without assuming their lexical or execution order."""

    from datamimic_ce.engine.dsl.api import CompositeStatement, GenerateStatement, SetupStatement

    assert isinstance(root_stmt, SetupStatement)
    statements: list[object] = []

    def _walk(stmt: object) -> None:
        if isinstance(stmt, GenerateStatement):
            statements.append(stmt)
        if isinstance(stmt, CompositeStatement):
            for child in stmt.sub_statements:
                _walk(child)

    for statement in root_stmt.sub_statements:
        _walk(statement)
    return tuple(statements)


def _memstore_producers(
    root_stmt: object,
    memstore_ids: set[str],
) -> tuple[_MemstoreProducer, ...]:
    from datamimic_ce.engine.dsl.api import GenerateStatement
    from datamimic_ce.engine.io.api import resolve_target_entity

    producers: list[_MemstoreProducer] = []
    for statement in _generate_statements(root_stmt):
        if not isinstance(statement, GenerateStatement):
            continue
        entity = resolve_target_entity(
            statement.target_entity,
            statement.type,
            statement.name,
        )
        for source_id in sorted(statement.targets & memstore_ids):
            producers.append(
                _MemstoreProducer(
                    source_id=source_id,
                    entity=entity,
                    product=capture_product_name(statement.full_name),
                )
            )
    return tuple(producers)


def _memstore_source_binding(
    stmt: object,
    *,
    memstore_ids: set[str],
    producers: tuple[_MemstoreProducer, ...],
) -> _MemstoreSourceBinding | None:
    from datamimic_ce.engine.dsl.api import EL_GENERATE, GenerateStatement
    from datamimic_ce.engine.dsl.vocabulary.source_capabilities import source_file_format_for
    from datamimic_ce.engine.io.api import resolve_source_entity

    if not isinstance(stmt, GenerateStatement) or stmt.source not in memstore_ids:
        return None
    if source_file_format_for(EL_GENERATE, stmt.source, stmt.type) is not None:
        return None
    entity = resolve_source_entity(stmt.source_entity, stmt.type, stmt.name)
    candidates = tuple(
        producer for producer in producers if producer.source_id == stmt.source and producer.entity == entity
    )
    if len(candidates) == 1:
        status = _MemstoreBindingStatus.RESOLVED
    elif candidates:
        status = _MemstoreBindingStatus.AMBIGUOUS
    else:
        status = _MemstoreBindingStatus.MISSING
    return _MemstoreSourceBinding(
        source_id=stmt.source,
        entity=entity,
        status=status,
        producers=candidates,
    )


def _dry_run_hazards(root_stmt: object) -> tuple[bool, bool]:
    from datamimic_ce.engine.dsl.api import CompositeStatement, ExecuteStatement, IncludeStatement

    has_execute = False
    has_unbounded_include = False
    pending = [root_stmt]
    while pending:
        stmt = pending.pop()
        if isinstance(stmt, ExecuteStatement):
            has_execute = True
        elif isinstance(stmt, IncludeStatement) and not stmt.uri.endswith(".properties"):
            has_unbounded_include = True
        elif isinstance(stmt, CompositeStatement):
            pending.extend(stmt.sub_statements)
    return has_execute, has_unbounded_include


# One stripped file target of a product: (exporter name in the registry, ctor params).
_FileTarget = tuple[str, dict[str, object]]
# product full_name -> basename, stripped file targets, resolved setup defaults
_StrippedTargets = dict[str, tuple[str, list[_FileTarget], str, str]]


def _parent_capture_name(stmt: object) -> str | None:
    from datamimic_ce.engine.dsl.api import GenerateStatement, Statement

    if not isinstance(stmt, Statement):
        return None
    parent = stmt.parent_stmt
    while parent is not None and not isinstance(parent, GenerateStatement):
        parent = parent.parent_stmt
    return capture_product_name(parent.full_name) if isinstance(parent, GenerateStatement) else None


def _source_row_count(
    stmt: object,
    *,
    descriptor_dir: Path | None,
    default_separator: str,
) -> int | None:
    """Return a file source's statically observable remaining rows, if supported."""

    from datamimic_ce.engine.dsl.api import EL_GENERATE, GenerateStatement
    from datamimic_ce.engine.dsl.vocabulary.source_capabilities import SourceFileFormat, source_file_format_for
    from datamimic_ce.engine.io.api import CountSourceRequest, count_source

    if not isinstance(stmt, GenerateStatement) or descriptor_dir is None or stmt.source is None:
        return None
    source_format = source_file_format_for(EL_GENERATE, stmt.source, stmt.type)
    if source_format is None or source_format is SourceFileFormat.DBUNIT_XML:
        return None
    try:
        rows = count_source(
            CountSourceRequest(
                source=stmt.source,
                source_id=(stmt.full_name, stmt.source),
                descriptor_dir=descriptor_dir,
                element=EL_GENERATE,
                source_type=stmt.type,
                source_entity=stmt.source_entity,
                name=stmt.name,
                separator=stmt.separator,
                default_separator=default_separator,
                selector=stmt.selector,
                iteration_selector=None,
            ),
            None,
            None,
        )
    except Exception:
        # This is evidence discovery, not execution. The canonical runtime reports
        # the real file error; failure to prove a length must remain UNKNOWN.
        return None
    return None if rows is None else max(0, rows - stmt.offset)


def _range_upper_bound(stmt: object) -> int | None:
    from datamimic_ce.engine.dsl.api import GenerateStatement

    if not isinstance(stmt, GenerateStatement):
        return None
    if stmt.max_count is not None:
        return stmt.max_count
    if stmt.min_count is not None:
        return stmt.min_count + 5
    return None


def _static_count(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _parse_buffered_targets(targets: set[str]) -> list[_FileTarget]:
    """The subset of raw target strings that are buffered FILE exporters, parsed to
    (name, params). Membership in the exporter registry is the dispatch — memstores,
    clients, Console/Log never appear there, so they can never be smoked."""
    from datamimic_ce.engine.dsl.parsers.input.target import parse_function_string
    from datamimic_ce.engine.io.api import buffered_exporter_names

    parsed: list[_FileTarget] = []
    buffered_names = buffered_exporter_names()
    for raw in sorted(targets):
        try:
            entries = parse_function_string(raw)
        except ValueError:
            continue  # malformed target string — the engine's own path reports it
        for entry in entries:
            if entry["function_name"] in buffered_names:
                parsed.append((entry["function_name"], entry.get("params") or {}))
    return parsed


def neutralize_for_dry_run(
    root_stmt: object,
    *,
    max_count: int,
    allow_side_effects: bool,
    stripped_file_targets: _StrippedTargets | None = None,
    product_budgets: _ProductBudgets | None = None,
    descriptor_dir: Path | None = None,
    workspace_root: Path | None = None,
) -> None:
    """Statement transformer: cap counts, keep only memstore targets, force 1 process.
    When a collector dict is given, the FILE targets removed from each product are
    recorded so smoke_export can replay the captured rows through them afterwards."""
    from datamimic_ce.engine.dsl.api import (
        CompositeStatement,
        DatabaseStatement,
        GenerateStatement,
        MongoDBStatement,
        SetupStatement,
    )
    from datamimic_ce.engine.io.api import resolve_target_entity

    assert isinstance(root_stmt, SetupStatement)
    has_execute, has_include = _dry_run_hazards(root_stmt)
    if (has_execute and not allow_side_effects) or has_include:
        raise _BoundedPolicyRefusal("bounded execution refuses execute or unresolved include side effects")
    memstores = _memstore_ids(root_stmt)
    memstore_producers = _memstore_producers(root_stmt, memstores)
    root_stmt.num_process = 1

    default_separator = root_stmt.default_separator or "|"
    default_line_separator = root_stmt.default_line_separator or "\n"

    def _neutralize(stmt: object) -> None:
        if not allow_side_effects and isinstance(stmt, (DatabaseStatement, MongoDBStatement)):
            stmt.model.read_only = True
        if isinstance(stmt, DatabaseStatement) and descriptor_dir is not None:
            from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
            from datamimic_ce.engine.io.api import sqlite_database_path

            if stmt.model.dbms is Dbms.SQLITE and stmt.model.database is not None:
                private_root = workspace_root or descriptor_dir
                database = (private_root / sqlite_database_path(stmt.model.database)).resolve(strict=False)
                if not database.is_relative_to(private_root):
                    raise _BoundedPolicyRefusal("SQLite source resolves outside the private bounded workspace")
        if isinstance(stmt, GenerateStatement):
            if not allow_side_effects:
                if stripped_file_targets is not None:
                    file_targets = _parse_buffered_targets(stmt.targets - memstores)
                    if file_targets:
                        # same basename resolution as the real exporter factory
                        basename = resolve_target_entity(stmt.target_entity, None, stmt.name)
                        stripped_file_targets[stmt.full_name] = (
                            basename,
                            file_targets,
                            default_separator,
                            default_line_separator,
                        )
                stmt.targets = {t for t in stmt.targets if t in memstores}
            stmt.num_process = 1
            requested = _static_count(stmt.count)
            source_rows = _source_row_count(
                stmt,
                descriptor_dir=descriptor_dir,
                default_separator=default_separator,
            )
            memstore_source = _memstore_source_binding(
                stmt,
                memstore_ids=memstores,
                producers=memstore_producers,
            )
            from datamimic_ce.engine.dsl.api import SourceDistribution

            source_exhaustible = (
                source_rows is not None and not stmt.cyclic and stmt.distribution is not SourceDistribution.CUMULATED
            )
            range_bound = _range_upper_bound(stmt) if stmt.count is None else None
            time_series = stmt.get_time_series_config()
            output_multiplier = time_series.ticks_per_series if time_series is not None else 1
            cap_applied = False
            bounded_without_cap = False
            reason = "runtime cardinality is not statically known"

            if requested is not None:
                count_kind = _CountBoundaryKind.STATIC
                bounded_without_cap = requested <= max_count
                if not bounded_without_cap:
                    stmt.count = str(max_count)
                    cap_applied = True
                    reason = f"static count {requested} exceeds per-invocation limit {max_count}"
                else:
                    reason = f"static count {requested} is within the per-invocation limit"
            elif stmt.count is not None:
                count_kind = _CountBoundaryKind.DYNAMIC
                # Dynamic expressions are evaluated only with a runtime context. Replacing
                # them is the only pre-execution bound that cannot be bypassed by the script.
                stmt.count = str(max_count)
                cap_applied = True
                reason = "dynamic count was replaced by the per-invocation limit"
            elif range_bound is not None:
                count_kind = _CountBoundaryKind.RANGE
                bounded_without_cap = range_bound <= max_count
                if not bounded_without_cap:
                    stmt.count = str(max_count)
                    cap_applied = True
                    reason = f"count range can exceed per-invocation limit {max_count}"
                else:
                    reason = f"count range has static upper bound {range_bound}"
            elif source_rows is not None:
                count_kind = _CountBoundaryKind.SOURCE
                bounded_without_cap = source_rows <= max_count
                if not bounded_without_cap:
                    stmt.count = str(max_count)
                    cap_applied = True
                    reason = f"file source has {source_rows} rows, above limit {max_count}"
                else:
                    reason = f"file source has {source_rows} statically observable rows"
            else:
                count_kind = _CountBoundaryKind.SOURCE
                # Includes DB, Mongo, memstore, scripted, and unresolved sources. The
                # explicit count bypasses their potentially unbounded cardinality scans.
                stmt.count = str(max_count)
                cap_applied = True

            if product_budgets is not None:
                name = capture_product_name(stmt.full_name)
                requested_per_parent: int | None = requested
                if requested_per_parent is None and range_bound is None:
                    requested_per_parent = source_rows
                product_budgets[name] = _ProductBudget(
                    name=name,
                    parent_name=_parent_capture_name(stmt),
                    requested_per_parent=requested_per_parent,
                    explicit_count=requested is not None,
                    count_kind=count_kind,
                    source_rows_per_parent=source_rows,
                    source_exhaustible=source_exhaustible,
                    memstore_source=memstore_source,
                    source_offset=stmt.offset,
                    cyclic=bool(stmt.cyclic),
                    output_multiplier=output_multiplier,
                    bounded_without_cap=bounded_without_cap,
                    cap_applied=cap_applied,
                    reason=reason,
                )
        if isinstance(stmt, CompositeStatement):
            for sub in stmt.sub_statements:
                _neutralize(sub)

    for stmt in root_stmt.sub_statements:
        _neutralize(stmt)


def _smoke_exporter(
    descriptor_dir: Path,
    task_id: str,
    basename: str,
    full_name: str,
    rows: list[dict[str, object]],
    exporter_name: str,
    params: dict[str, object],
    default_separator: str,
    default_line_separator: str,
) -> Diagnostic | None:
    from datamimic_ce.engine.io.api import smoke_export

    try:
        written_rows = smoke_export(
            SmokeExportRequest(
                descriptor_dir=descriptor_dir,
                task_id=task_id,
                basename=basename,
                full_name=full_name,
                rows=rows,
                exporter_name=exporter_name,
                params=params,
                default_separator=default_separator,
                default_line_separator=default_line_separator,
            )
        )
        if written_rows == len(rows):
            return None
        return Diagnostic(
            rule=RULE_RUNTIME_ERROR,
            severity=RuleSeverity.ERROR,
            message=(
                f"{exporter_name} smoke export wrote {written_rows} of {len(rows)} captured rows for '{full_name}'"
            ),
            fix_hint=(
                f"The {exporter_name} exporter did not write every captured row. "
                "Check its write path before using this target."
            ),
            element="generate",
            path="/setup",
            name=full_name,
        )
    except Exception as err:
        return Diagnostic(
            rule=RULE_RUNTIME_ERROR,
            severity=RuleSeverity.ERROR,
            message=f"{exporter_name} smoke export failed for '{full_name}': {err}",
            fix_hint=(
                f"A generated value cannot be written by the {exporter_name} exporter "
                "(the error names the offending type). Cast the field in the DSL "
                f'(e.g. type="string" or script="str(...)"), or drop {exporter_name} '
                "from target=."
            ),
            element="generate",
            path="/setup",
            name=full_name,
        )


_CapturedRows = dict[NonEmptyStrictStr, tuple[dict[StrictStr, object], ...]]
_CAPTURE_ROWS = TypeAdapter(
    dict[NonEmptyStrictStr, list[dict[StrictStr, object]] | tuple[dict[StrictStr, object], ...]]
)
_MAX_WORKER_REPLY_BYTES = 64 * 1024 * 1024


def _decode_worker_payload(payload: bytes) -> object:
    """Accept passive CE/native values without executing arbitrary pickle reducers."""
    from datetime import date, datetime, timedelta, timezone
    from datetime import time as datetime_time
    from decimal import Decimal
    from json import JSONDecodeError
    from uuid import UUID

    from datamimic_ce.errors import base as errors
    from datamimic_ce.errors.codes import DomainErrorCode, ErrorCode, IssueCode
    from datamimic_ce.errors.context import DescriptorLocation

    allowed = (
        _WorkerSuccess,
        _WorkerFailure,
        _ProductBudget,
        _CountBoundaryKind,
        _MemstoreProducer,
        _MemstoreSourceBinding,
        _MemstoreBindingStatus,
        SmokeExportCapture,
        date,
        datetime,
        datetime_time,
        timedelta,
        timezone,
        Decimal,
        UUID,
        DomainErrorCode,
        ErrorCode,
        IssueCode,
        DescriptorLocation,
        errors.DomainError,
        errors.InvalidLocaleError,
        errors.UserErrorBase,
        errors.UserValueError,
        errors.UserRuntimeError,
        errors.InvalidDatasetError,
        errors.DateTimeConversionError,
        errors.EntityInitError,
        errors.InvalidSourceError,
        errors.MissingMemstoreProductError,
        errors.RuleEvaluationError,
        errors.ExportConfigError,
        errors.ExternalFailureCause,
        errors.IncludeError,
        errors.GeneratorConfigError,
        errors.ConditionEvaluationError,
        errors.ParserValidationError,
        errors.ClientConfigError,
        errors.TaskConfigError,
        errors.OperationError,
        errors.RuntimeConfigError,
        errors._restore_domain_error,
        errors._restore_locale_error,
        errors._restore_user_error,
        JSONDecodeError,
        ValidationError,
        Exception,
        ValueError,
        TypeError,
        KeyError,
        RuntimeError,
        AttributeError,
        IndexError,
        ZeroDivisionError,
        OverflowError,
        OSError,
        FileNotFoundError,
        PermissionError,
        TimeoutError,
        AssertionError,
        NameError,
        ImportError,
        SyntaxError,
        NotImplementedError,
    )
    globals_by_name: dict[tuple[str, str], object] = {(value.__module__, value.__name__): value for value in allowed}

    def validation_error_constructor(owner: object, name: str) -> object:
        # Pydantic's native pickle uses this exact classmethod lookup.
        if owner is ValidationError and name == "from_exception_data":
            return ValidationError.from_exception_data
        raise pickle.UnpicklingError("bounded reply requested an unsupported attribute")

    globals_by_name[("builtins", "getattr")] = validation_error_constructor

    class PassiveUnpickler(pickle.Unpickler):
        def find_class(self, module: str, name: str) -> object:
            try:
                return globals_by_name[(module, name)]
            except KeyError as error:
                raise pickle.UnpicklingError("bounded reply contains an unsupported global") from error

    if len(payload) > _MAX_WORKER_REPLY_BYTES:
        raise pickle.UnpicklingError("bounded reply exceeds its byte limit")
    stream = io.BytesIO(payload)
    result = PassiveUnpickler(stream).load()
    if stream.read(1):
        raise pickle.UnpicklingError("bounded reply contains trailing data")
    return result


def _validated_capture_rows(captured: object) -> _CapturedRows:
    validate_capture_values(captured)
    try:
        validated = _CAPTURE_ROWS.validate_python(captured, strict=True)
    except (TypeError, ValueError) as error:
        raise ValueError("capture contains an invalid product or row") from error
    return {name: tuple(rows) for name, rows in validated.items()}


def _validated_worker_success(message: _WorkerSuccess, max_count: int | None = None) -> _WorkerSuccess:
    _validated_capture_rows(message.captured)
    # Reconstruct from the complete state: instance revalidation discards forged extra fields.
    validated_budgets = []
    for budget in message.budgets:
        if budget.memstore_source is not None:
            original_binding = budget.memstore_source
            _MemstoreSourceBinding(**original_binding.__dict__)
            for producer in original_binding.producers:
                _MemstoreProducer(**producer.__dict__)
        validated_budgets.append(_ProductBudget(**budget.__dict__))
    SmokeExportCapture(**message.smoke_export.__dict__)
    message = _WorkerSuccess(**message.__dict__)
    message = _WorkerSuccess(
        message.captured, tuple(validated_budgets), message.smoke_diagnostics, message.smoke_export
    )
    names = [budget.name for budget in message.budgets]
    if len(names) != len(set(names)):
        raise ValueError("duplicate capture provenance")
    budgets = {budget.name: budget for budget in message.budgets}
    if set(message.captured) != set(budgets):
        raise ValueError("capture is missing product provenance")
    for budget in message.budgets:
        if budget.parent_name is not None and budget.parent_name not in budgets:
            raise ValueError("capture provenance references a missing parent")
        if budget.bounded_without_cap and budget.cap_applied:
            raise ValueError("capture provenance has contradictory bounds")
        if budget.explicit_count and budget.requested_per_parent is None:
            raise ValueError("explicit count provenance requires the requested count")
        parent = budget.parent_name
        ancestry = {budget.name}
        while parent is not None:
            if parent in ancestry:
                raise ValueError("capture parent provenance contains a cycle")
            ancestry.add(parent)
            parent = budgets[parent].parent_name
        if max_count is not None:
            parent_rows = len(message.captured.get(budget.parent_name, ())) if budget.parent_name else 1
            limit = max_count * parent_rows * budget.output_multiplier
            if len(message.captured.get(budget.name, ())) > limit:
                raise ValueError("capture rows exceed the full nested product bound")
        binding = budget.memstore_source
        if binding is not None:
            expected = {_MemstoreBindingStatus.MISSING: 0, _MemstoreBindingStatus.RESOLVED: 1}
            if binding.status in expected and len(binding.producers) != expected[binding.status]:
                raise ValueError("invalid memstore provenance cardinality")
            if binding.status is _MemstoreBindingStatus.AMBIGUOUS and len(binding.producers) < 2:
                raise ValueError("ambiguous memstore provenance needs multiple producers")
            if any(
                producer.product not in budgets or producer.source_id != binding.source_id
                for producer in binding.producers
            ):
                raise ValueError("invalid memstore producer provenance")
    smoke = message.smoke_export
    counters = (smoke.applicable_exporters, smoke.attempted_exporters, smoke.failed_exporters)
    if type(smoke.requested) is not bool or any(type(value) is not int or value < 0 for value in counters):
        raise ValueError("invalid smoke-export counters")
    if smoke.failed_exporters > smoke.attempted_exporters or smoke.attempted_exporters > smoke.applicable_exporters:
        raise ValueError("inconsistent smoke-export counters")
    if not smoke.requested and (any(counters) or message.smoke_diagnostics):
        raise ValueError("unrequested smoke-export contains execution facts")
    for diagnostic in message.smoke_diagnostics:
        Diagnostic.model_validate(diagnostic)
    return message


def _smoke_export(
    captured: Mapping[str, Sequence[object]],
    stripped: _StrippedTargets,
) -> tuple[list[Diagnostic], SmokeExportCapture]:
    """Replay the captured rows through each stripped file exporter inside a temp dir
    (write + finalize — the two phases where serialization crashes live). The tempdir
    context manager guarantees zero artifacts. Failures become DM002 diagnostics."""
    captured = _validated_capture_rows(captured)
    diagnostics: list[Diagnostic] = []
    applicable_exporters = sum(len(file_targets) for _basename, file_targets, _, _ in stripped.values())
    attempted_exporters = 0
    failed_exporters = 0
    with tempfile.TemporaryDirectory(prefix="datamimic_smoke_") as tmp:
        descriptor_dir = Path(tmp).resolve()
        task_id = f"smoke_{uuid.uuid4().hex}"
        # Export readback is contained in its own private artifact directory.
        with resource_reader_scope(AuthoringWorkspaceContext(descriptor_dir).read_resource_bytes):
            for full_name, (basename, file_targets, default_separator, default_line_separator) in sorted(
                stripped.items()
            ):
                rows = list(captured.get(capture_product_name(full_name), ()))
                if not rows:
                    continue
                for exporter_name, params in file_targets:
                    attempted_exporters += 1
                    diagnostic = _smoke_exporter(
                        descriptor_dir,
                        task_id,
                        basename,
                        full_name,
                        rows,
                        exporter_name,
                        params,
                        default_separator,
                        default_line_separator,
                    )
                    if diagnostic is not None:
                        failed_exporters += 1
                        diagnostics.append(diagnostic)
    return diagnostics, SmokeExportCapture(
        requested=True,
        applicable_exporters=applicable_exporters,
        attempted_exporters=attempted_exporters,
        failed_exporters=failed_exporters,
    )


@contextmanager
def _suppress_worker_stderr() -> Iterator[None]:
    """Silence engine logs at FD 2 inside the isolated dry-run child only."""

    saved_stderr: int | None = None
    null_stderr: int | None = None
    redirected = False
    try:
        null_stderr = os.open(os.devnull, os.O_WRONLY)
        saved_stderr = os.dup(2)
        os.dup2(null_stderr, 2)
        redirected = True
    except OSError:
        # A closed or unavailable stderr must not turn an otherwise valid dry-run
        # into a runtime failure. The worker still returns structured evidence by IPC.
        pass
    try:
        yield
    finally:
        if redirected and saved_stderr is not None:
            with suppress(OSError):
                os.dup2(saved_stderr, 2)
        if saved_stderr is not None:
            os.close(saved_stderr)
        if null_stderr is not None:
            os.close(null_stderr)


def _run_engine_capture(
    path: Path,
    max_count: int,
    allow_side_effects: bool,
    smoke_export: bool,
    *,
    profile_loader: Callable[[Path, str], dict[str, str]] | None = None,
    environment_properties: dict[str, str] | None = None,
    logical_descriptor_path: str | None = None,
    workspace_root: Path | None = None,
) -> _WorkerMessage:
    """Execute and capture exactly one engine run inside the cancellable process."""

    with _suppress_worker_stderr(), descriptor_scope(logical_descriptor_path or path.name):
        from functools import partial

        from datamimic_ce.engine.runtime.api import create_run_session
        from datamimic_ce.engine.runtime.contracts import RunRequest

        budgets: _ProductBudgets = {}
        stripped: _StrippedTargets | None = {} if smoke_export else None
        try:
            session = create_run_session(
                RunRequest(
                    descriptor_path=path,
                    task_id=f"dryrun_{uuid.uuid4().hex}",
                    test_mode=True,
                    profile_loader=profile_loader,
                    platform_props=environment_properties,
                    statement_transformer=partial(
                        neutralize_for_dry_run,
                        max_count=max_count,
                        allow_side_effects=allow_side_effects,
                        stripped_file_targets=stripped,
                        product_budgets=budgets,
                        descriptor_dir=path.parent,
                        workspace_root=workspace_root,
                    ),
                ),
            )
            session.execute()
            capture = session.capture_test_result()
            raw_capture = _validated_capture_rows(capture if capture is not None else {})
            if set(raw_capture) - set(budgets):
                raise ValueError("runtime capture has no canonical product provenance")
            # The engine omits zero-row products; keep their explicit empty capture.
            raw_capture = {name: raw_capture.get(name, ()) for name in budgets}
            _validated_worker_success(
                _WorkerSuccess(raw_capture, tuple(budgets.values()), (), SmokeExportCapture.not_requested()),
                max_count=max_count,
            )
            if stripped is None:
                smoke_diagnostics: list[Diagnostic] = []
                smoke_export_capture = SmokeExportCapture.not_requested()
            else:
                smoke_diagnostics, smoke_export_capture = _smoke_export(raw_capture, stripped)
            captured = raw_capture
            message: _WorkerMessage = _WorkerSuccess(
                captured=captured,
                budgets=tuple(sorted(budgets.values(), key=lambda budget: budget.name)),
                smoke_diagnostics=tuple(diagnostic.model_dump(mode="json") for diagnostic in smoke_diagnostics),
                smoke_export=smoke_export_capture,
            )
        except Exception as err:
            if is_user_error(err):
                from datamimic_ce.engine.io.api import (
                    normalize_error_cause_for_transport,
                    normalize_exporter_error_cause_for_transport,
                )

                normalize_exporter_error_cause_for_transport(err)
                normalize_error_cause_for_transport(err)
            # The process is the untyped runtime boundary: every engine exception must
            # become a stable DM002 response rather than killing the authoring transport.
            message = _WorkerFailure(
                message=str(err) or type(err).__name__,
                fix_hint=_runtime_hint(err),
                error=err if is_user_error(err) else None,
                policy_refusal=isinstance(err, _BoundedPolicyRefusal),
            )
        return message


def _capture_evidence(
    budget: _ProductBudget | None,
    *,
    observed: int,
    max_count: int,
    observed_by_name: dict[str, int],
) -> ProductCaptureEvidence:
    parent_observed = 1
    if budget is not None and budget.parent_name is not None:
        parent_observed = observed_by_name.get(budget.parent_name, 0)
    output_multiplier = budget.output_multiplier if budget is not None else 1
    limit = max(1, max_count * parent_observed * output_multiplier)
    if budget is None:
        return ProductCaptureEvidence(
            status=CaptureStatus.UNKNOWN,
            requested=None,
            observed=observed,
            limit=limit,
            reason="runtime product has no transformed statement-boundary evidence",
        )

    requested = (
        budget.requested_per_parent * parent_observed * output_multiplier
        if budget.requested_per_parent is not None
        else None
    )
    available = (
        budget.source_rows_per_parent * parent_observed * output_multiplier
        if budget.source_rows_per_parent is not None
        else None
    )
    if (
        budget.source_exhaustible
        and available is not None
        and observed == available
        and (not budget.explicit_count or requested is None or requested >= available)
    ):
        return ProductCaptureEvidence(
            status=CaptureStatus.EXHAUSTED,
            requested=requested,
            observed=observed,
            limit=limit,
            reason=f"finite file source exhausted after {available} available rows",
        )
    if budget.cap_applied and observed == limit:
        return ProductCaptureEvidence(
            status=CaptureStatus.CAPPED,
            requested=requested,
            observed=observed,
            limit=limit,
            reason=budget.reason,
        )
    if budget.bounded_without_cap and (requested is None or observed == requested):
        return ProductCaptureEvidence(
            status=CaptureStatus.COMPLETE,
            requested=requested,
            observed=observed,
            limit=limit,
            reason=budget.reason,
        )
    return ProductCaptureEvidence(
        status=CaptureStatus.UNKNOWN,
        requested=requested,
        observed=observed,
        limit=limit,
        reason=(
            f"{budget.reason}; observed rows do not prove whether the runtime source "
            "or dynamic cardinality was exhausted"
        ),
    )


def _unknown_from(
    evidence: ProductCaptureEvidence,
    reason: str,
) -> ProductCaptureEvidence:
    return ProductCaptureEvidence(
        status=CaptureStatus.UNKNOWN,
        requested=evidence.requested,
        observed=evidence.observed,
        limit=evidence.limit,
        reason=reason,
    )


def _memstore_capture_evidence(
    budget: _ProductBudget,
    base: ProductCaptureEvidence,
    *,
    producer_evidence: ProductCaptureEvidence,
    producer_observed: int,
    parent_observed: int,
) -> ProductCaptureEvidence:
    binding = budget.memstore_source
    if binding is None:
        return base
    if not producer_evidence.complete:
        return _unknown_from(
            base,
            (
                f"memstore '{binding.source_id}' entity '{binding.entity}' depends on "
                "a producer capture that is not proven complete"
            ),
        )
    available_per_parent = max(0, producer_observed - budget.source_offset)
    available = available_per_parent * parent_observed * budget.output_multiplier
    if budget.count_kind is _CountBoundaryKind.DYNAMIC:
        return (
            base
            if base.status is CaptureStatus.CAPPED
            else _unknown_from(
                base,
                "dynamic count replacement prevents a complete memstore-read proof",
            )
        )
    if budget.cyclic:
        return _unknown_from(
            base,
            "cyclic memstore reads do not provide finite exhaustion evidence",
        )
    if budget.count_kind is _CountBoundaryKind.SOURCE:
        return _source_memstore_capture_evidence(base, available)
    if budget.count_kind is _CountBoundaryKind.STATIC and base.requested is not None:
        return _static_memstore_capture_evidence(base, available)
    return base


def _source_memstore_capture_evidence(
    base: ProductCaptureEvidence,
    available: int,
) -> ProductCaptureEvidence:
    if available > base.limit:
        if base.observed == base.limit:
            return ProductCaptureEvidence(
                status=CaptureStatus.CAPPED,
                requested=available,
                observed=base.observed,
                limit=base.limit,
                reason=(f"finite memstore source has {available} available rows, above capture limit {base.limit}"),
            )
        return _unknown_from(base, "memstore source did not reach its proven finite window")
    if base.observed == available:
        return ProductCaptureEvidence(
            status=CaptureStatus.EXHAUSTED,
            requested=available,
            observed=base.observed,
            limit=base.limit,
            reason=(f"uniquely resolved memstore producer was fully read: {available} finite rows"),
        )
    return _unknown_from(base, "memstore source did not exhaust its proven finite window")


def _static_memstore_capture_evidence(
    base: ProductCaptureEvidence,
    available: int,
) -> ProductCaptureEvidence:
    if base.requested is None or base.observed != min(base.requested, available):
        return base
    if base.requested >= available:
        return ProductCaptureEvidence(
            status=CaptureStatus.EXHAUSTED,
            requested=base.requested,
            observed=base.observed,
            limit=base.limit,
            reason=(f"static request reached all {available} rows of the uniquely resolved memstore producer"),
        )
    if base.requested <= base.limit:
        return ProductCaptureEvidence(
            status=CaptureStatus.COMPLETE,
            requested=base.requested,
            observed=base.observed,
            limit=base.limit,
            reason="static memstore read completed within the finite source window",
        )
    return base


def _capture_evidence_by_product(
    budgets: _ProductBudgets,
    captured: Mapping[str, tuple[object, ...]],
    *,
    max_count: int,
) -> dict[str, ProductCaptureEvidence]:
    """Resolve ancestry and memstore provenance recursively, independent of name order."""

    return _CaptureEvidenceResolver(budgets, captured, max_count).resolve_all()


class _CaptureEvidenceResolver:
    """Resolve capture completeness from typed ancestry and memstore facts."""

    def __init__(
        self,
        budgets: _ProductBudgets,
        captured: Mapping[str, tuple[object, ...]],
        max_count: int,
    ) -> None:
        self._budgets = budgets
        self._observed = {name: len(rows) for name, rows in captured.items()}
        self._product_names = tuple(captured)
        self._max_count = max_count
        self._resolved: dict[str, ProductCaptureEvidence] = {}
        self._visiting: set[str] = set()

    def resolve_all(self) -> dict[str, ProductCaptureEvidence]:
        for product_name in self._product_names:
            self._resolve(product_name)
        return self._resolved

    def _resolve(self, name: str) -> ProductCaptureEvidence:
        existing = self._resolved.get(name)
        if existing is not None:
            return existing
        budget = self._budgets.get(name)
        base = _capture_evidence(
            budget,
            observed=self._observed.get(name, 0),
            max_count=self._max_count,
            observed_by_name=self._observed,
        )
        if name in self._visiting:
            return _unknown_from(
                base,
                "capture dependency cycle prevents a completeness proof",
            )
        self._visiting.add(name)
        evidence, dependency_blocked = self._parent_evidence(budget, base)
        if budget is not None and budget.memstore_source is not None and not dependency_blocked:
            evidence = self._memstore_evidence(budget, base)
        self._visiting.remove(name)
        self._resolved[name] = evidence
        return evidence

    def _parent_evidence(
        self,
        budget: _ProductBudget | None,
        base: ProductCaptureEvidence,
    ) -> tuple[ProductCaptureEvidence, bool]:
        if budget is None or budget.parent_name is None:
            return base, False
        if budget.parent_name not in self._observed:
            return _unknown_from(base, "parent product is missing from runtime capture"), True
        parent_evidence = self._resolve(budget.parent_name)
        if not parent_evidence.complete:
            return _unknown_from(base, "parent product capture is not proven complete"), True
        return base, False

    def _memstore_evidence(
        self,
        budget: _ProductBudget,
        base: ProductCaptureEvidence,
    ) -> ProductCaptureEvidence:
        binding = budget.memstore_source
        if binding is None:
            return base
        if binding.status is _MemstoreBindingStatus.MISSING:
            return _unknown_from(
                base,
                (f"memstore '{binding.source_id}' entity '{binding.entity}' has no captured producer"),
            )
        if binding.status is _MemstoreBindingStatus.AMBIGUOUS:
            return _unknown_from(
                base,
                (f"memstore '{binding.source_id}' entity '{binding.entity}' has multiple possible producers"),
            )
        return self._resolved_memstore_evidence(budget, binding, base)

    def _resolved_memstore_evidence(
        self,
        budget: _ProductBudget,
        binding: _MemstoreSourceBinding,
        base: ProductCaptureEvidence,
    ) -> ProductCaptureEvidence:
        producer = next(iter(binding.producers), None)
        if producer is None or producer.product not in self._observed:
            return _unknown_from(
                base,
                "resolved memstore producer is missing from runtime capture",
            )
        return _memstore_capture_evidence(
            budget,
            base,
            producer_evidence=self._resolve(producer.product),
            producer_observed=self._observed[producer.product],
            parent_observed=self._parent_observed(budget),
        )

    def _parent_observed(self, budget: _ProductBudget) -> int:
        if budget.parent_name is None:
            return 1
        return self._observed.get(budget.parent_name, 0)


def _captured_products(message: _WorkerSuccess, max_count: int) -> CapturedProducts:
    message = _validated_worker_success(message, max_count=max_count)
    budgets = {budget.name: budget for budget in message.budgets}
    evidence = _capture_evidence_by_product(budgets, message.captured, max_count=max_count)
    return CapturedProducts(
        products=tuple(
            CapturedProduct(name=name, rows=rows, capture=evidence[name])
            for name, rows in sorted(message.captured.items())
        ),
        max_count=max_count,
    )


def _decode_worker_message(payload: bytes, *, max_count: int | None = None) -> _WorkerMessage:
    message = _decode_worker_payload(payload)
    if isinstance(message, _WorkerSuccess):
        return _validated_worker_success(message, max_count=max_count)
    if isinstance(message, _WorkerFailure):
        message = _WorkerFailure(**message.__dict__)
        if message.error is not None and not isinstance(message.error, (UserErrorBase, DomainError)):
            raise ValueError("worker failure contains an unsupported error type")
        return message
    raise ValueError("worker returned an unknown envelope")
