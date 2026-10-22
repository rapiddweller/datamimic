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
from pathlib import Path, PurePosixPath

from bson import ObjectId
from lxml import etree
from pydantic import ConfigDict, StrictBool, StrictStr, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass

from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.capture import (
    MAX_CAPTURE_DEPTH,
    MAX_CAPTURE_ITEMS,
    CapturedObjectId,
    CapturedProduct,
    CapturedProducts,
    CaptureStatus,
    CaptureValue,
    ProductCaptureEvidence,
    SmokeExportCapture,
    validate_capture_values,
)
from datamimic_ce.authoring.domain.common import NonEmptyStrictStr, NonNegativeStrictInt, PositiveStrictInt
from datamimic_ce.authoring.domain.rule_catalog import RuleSeverity
from datamimic_ce.authoring.domain.xml_diagnostics import Diagnostic
from datamimic_ce.engine.dsl.api import NAME_SEPARATOR, capture_product_name, resource_reader_scope
from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import ATTR_COUNT
from datamimic_ce.engine.io.contracts import SmokeExportRequest
from datamimic_ce.errors import (
    GUIDANCE_COUNT_SCOPE,
    DomainError,
    ErrorCode,
    ExternalFailureCause,
    GeneratorConfigError,
    MissingMemstoreProductError,
    UserErrorBase,
    is_user_error,
)
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
    UNRESOLVED_INCLUDES = "unresolved_includes"


@dataclass(frozen=True, config=ConfigDict(extra="forbid", strict=True, revalidate_instances="always"))
class _MemstoreSourceBinding:
    """Typed runtime routing fact for one generate reading a memstore entity."""

    source_id: NonEmptyStrictStr
    entity: str | None
    status: _MemstoreBindingStatus
    producers: tuple[_MemstoreProducer, ...]


@dataclass(frozen=True, config=ConfigDict(extra="forbid", strict=True, revalidate_instances="always"))
class _WorkerSuccess:
    captured: dict[NonEmptyStrictStr, tuple[dict[StrictStr, CaptureValue], ...]]
    budgets: tuple[_ProductBudget, ...]
    smoke_diagnostics: tuple[dict[str, object], ...]
    smoke_export: SmokeExportCapture
    source_accesses: tuple[tuple[NonEmptyStrictStr, PositiveStrictInt], ...] = ()
    # Workspace-relative POSIX paths of snapshot files the contained run opened for reading.
    read_files: tuple[NonEmptyStrictStr, ...] = ()


@dataclass(frozen=True, config=ConfigDict(extra="forbid", strict=True, revalidate_instances="always"))
class _WorkerFailure:
    message: NonEmptyStrictStr
    fix_hint: NonEmptyStrictStr
    error: object | None = None
    policy_refusal: StrictBool = False
    # Empty unless the refusal names the included step and element that breaks the policy.
    policy_path: tuple[NonEmptyStrictStr, ...] = ()


class _BoundedPolicyRefusal(ValueError):
    """A parsed operation cannot inherit bounded execution guarantees."""

    def __init__(self, message: str, path: tuple[str, ...] = ()) -> None:
        ValueError.__init__(self, message)
        self.path = path


class _IncludeBudgetExceeded(_BoundedPolicyRefusal):
    """The include graph's aggregate bytes exceed the budget."""


_WorkerMessage = _WorkerSuccess | _WorkerFailure


_SCOPE_HINT = (
    "A script may reference an unavailable name or an unexpected value structure. Check spelling, definition order,"
    " and value shape. Names in the current scope can resolve bare or via this.name; existing outermost bare names"
    " take precedence on collisions. Use parent.name for the immediate enclosing scope, root.name for an"
    " outermost field, or a qualified scope path to select the intended value. Intermediate ancestor names are"
    " not automatically available bare. CSV columns arrive as strings (cast: int(parent.col))."
)


_CONTAINMENT_HINT = (
    "Bounded execution writes only new files inside its private workspace, never the workspace files it was "
    "checked against, and starts no process (#361). Deliver data "
    "through the model's targets, or use authoring run --allow-side-effects when the write is intended."
)


def _runtime_hint(err: Exception) -> str:
    current: BaseException | None = err
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, MissingMemstoreProductError):
            return current.guidance
        if isinstance(current, UserErrorBase) and current.issue_code is not None:
            issue = get_issue_definition(current.issue_code)
            if current.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED:
                if isinstance(current.__cause__, PermissionError):
                    return _CONTAINMENT_HINT
                if current.location is None or current.location.attribute != ATTR_COUNT:
                    return _SCOPE_HINT
                # Only a failed name lookup is a scope problem; 1/0 or int('text') in a count is not.
                named = isinstance(current.__cause__, NameError | AttributeError)
                return GUIDANCE_COUNT_SCOPE if named else issue.resolution
            return issue.guidance or issue.resolution
        if isinstance(current, DomainError) and current.hint:
            return current.hint
        if isinstance(current, PermissionError):
            return _CONTAINMENT_HINT
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
    unresolved_includes: bool = False,
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
    if unresolved_includes:
        status = _MemstoreBindingStatus.UNRESOLVED_INCLUDES
        candidates = ()
    elif len(candidates) == 1:
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


def _dry_run_hazards(root_stmt: object, *, includes_validated: bool) -> tuple[tuple[object, ...], bool]:
    from datamimic_ce.engine.dsl.api import CompositeStatement, ExecuteStatement, IncludeStatement

    executes: list[object] = []
    has_unbounded_include = False
    pending = [root_stmt]
    while pending:
        stmt = pending.pop()
        if isinstance(stmt, ExecuteStatement):
            executes.append(stmt)
        elif isinstance(stmt, IncludeStatement):
            if "{" in stmt.uri or not (
                stmt.uri.endswith(".properties") or (includes_validated and stmt.uri.endswith(".xml"))
            ):
                has_unbounded_include = True
        elif isinstance(stmt, CompositeStatement):
            pending.extend(stmt.sub_statements)
    return tuple(executes), has_unbounded_include


def _refuse_unbounded_execute(
    language: str | None,
    *,
    target: str | None,
    script: str | None,
    uri: str | None,
    inline: str | None,
    setup_level: bool,
    descriptor_dir: Path,
    seeded: bool,
) -> None:
    """Admit <execute> only as a setup-level Python library that passes the static library check (#332)."""
    from datamimic_ce.authoring.domain.script_semantics import admits_python_library, python_library_refusal
    from datamimic_ce.engine.dsl.api import ExecuteStatement, read_resource_bytes

    if not setup_level or not admits_python_library(language, target=target, script=script):
        raise _BoundedPolicyRefusal(
            "Bounded execution admits <execute> only as a setup-level Python library without target or script"
        )
    if uri is not None:
        try:
            raw = str(read_resource_bytes(descriptor_dir / uri), "utf-8")
        except (FileNotFoundError, UnicodeDecodeError):
            return  # the runtime reports the missing or unreadable script itself
        except ValueError as error:  # the contained reader refuses paths outside the private workspace
            raise _BoundedPolicyRefusal("Python library uri must name a file inside the workspace") from error
        origin = Path(uri).name
    else:
        raw = inline or ""
        origin = "inline <execute>"
    # Check exactly what ExecuteTask will run: it normalizes file and inline code alike.
    refusal = python_library_refusal(ExecuteStatement.normalize_python_source(raw), seeded=seeded)
    if refusal is not None:
        raise _BoundedPolicyRefusal(f"{origin}: {refusal.message()}. {refusal.remediation()}")


# Aggregate bytes one include graph may read; Build walks it in the authoring process, not in the bounded child.
_MAX_INCLUDE_GRAPH_BYTES = 64 * 1024 * 1024


def _literal_include_graph(entry: etree._Element, entry_path: Path) -> tuple[tuple[str, bytes], ...]:
    """The entry's literal include graph in execution order: (workspace-relative uri, file bytes) per ``.xml``
    step; ``.properties`` files are read for containment but not retained. Nested uris resolve against the entry
    directory, as the runtime resolves them. Raises _BoundedPolicyRefusal unless the graph is literal,
    setup-level, contained, acyclic and bounded in files and bytes; reads go through the active resource reader,
    so a contained reader refuses paths outside it."""
    from datamimic_ce.engine.dsl.api import parse_xml_source, read_resource_bytes

    descriptor_dir = entry_path.parent
    graph: list[tuple[str, bytes]] = []
    active = [os.path.abspath(entry_path)]
    visited = 0
    total = 0

    def visit(document: etree._Element) -> None:
        nonlocal visited, total
        if document.tag != "setup":
            raise _BoundedPolicyRefusal("XML include must contain a setup descriptor")
        for node in document.iter("include"):
            uri = node.get("uri", "")
            if (
                node.getparent() is not document
                or not uri
                or any(mark in uri for mark in "{\\:")
                or Path(uri).is_absolute()
            ):
                raise _BoundedPolicyRefusal("Bounded XML includes require literal setup-level workspace paths")
            if len(node):
                raise _BoundedPolicyRefusal("Bounded XML includes require a uri without an inline setup")
            suffix = PurePosixPath(uri).suffix
            if suffix not in {".xml", ".properties"}:
                raise _BoundedPolicyRefusal("Unsupported bounded include dependency type")
            dependency = descriptor_dir / uri
            data = read_resource_bytes(dependency)
            total += len(data)
            if total > _MAX_INCLUDE_GRAPH_BYTES:
                raise _IncludeBudgetExceeded("XML include dependency graph exceeds the aggregate byte budget")
            if suffix == ".xml":
                graph.append((uri, data))
                visited += 1
                identity = os.path.abspath(dependency)
                if identity in active or len(active) >= 64 or visited > 2000:
                    raise _BoundedPolicyRefusal("XML include dependency graph is cyclic or exceeds bounded limits")
                active.append(identity)
                visit(parse_xml_source(data))
                active.pop()

    visit(entry)
    return tuple(graph)


def _validate_bounded_includes(
    path: Path, *, allow_side_effects: bool
) -> tuple[set[str], tuple[_MemstoreProducer, ...] | None]:
    """Check the literal dependency graph before any task, without changing native parse order. Returns the
    graph's memstore ids and its run-wide memstore producers, or no producers when the entry includes no step."""
    from datamimic_ce.engine.dsl.api import (
        ExecuteStatement,
        get_element_definition,
        parse_consumer,
        parse_xml_file,
        parse_xml_source,
    )
    from datamimic_ce.engine.dsl.vocabulary.contracts.dsl_element import BoundedExecutionStrategy
    from datamimic_ce.engine.io.api import resolve_target_entity

    root = parse_xml_file(path)
    # Without steps the engine resolves properties includes itself and reports a missing file as a typed error.
    if all(PurePosixPath(node.get("uri", "")).suffix != ".xml" for node in root.iter("include")):
        return set(), None
    try:
        graph = _literal_include_graph(root, path)
    except _BoundedPolicyRefusal:
        raise
    except (OSError, ValueError) as error:
        # Every step is checked before any runs, so a missing file stops the whole graph.
        raise _BoundedPolicyRefusal("An included file is missing or lies outside the workspace") from error
    step_uris = tuple(uri for uri, _ in graph if PurePosixPath(uri).suffix == ".xml")
    steps = tuple(parse_xml_source(data) for uri, data in graph if PurePosixPath(uri).suffix == ".xml")
    documents = (root, *steps)
    seeded = root.get("rngSeed") is not None
    products: set[str] = set()
    memstores = {node.get("id", "") for document in documents for node in document.iter("memstore")} - {""}
    producers: list[_MemstoreProducer] = []

    def check(node: etree._Element, document: etree._Element, lineage: tuple[str, ...], uri: str | None) -> None:
        tag = node.tag
        if not isinstance(tag, str):
            raise _BoundedPolicyRefusal("Included descriptor element must have a text tag")
        # The root has no step uri; its refusals fall back to the descriptor path.
        where = () if uri is None else ("include", uri, tag)
        definition = get_element_definition(tag)
        if tag == "include":
            return  # the graph walk already checked every include
        if (
            definition is not None
            and definition.bounded_execution_profile.strategy is BoundedExecutionStrategy.PYTHON_LIBRARY
        ):
            if not allow_side_effects:
                try:
                    _refuse_unbounded_execute(
                        ExecuteStatement.language(node.get("type"), node.get("uri")),
                        target=node.get("target"),
                        script=node.get("script"),
                        uri=node.get("uri"),
                        inline=node.text,
                        setup_level=any(node is child for child in document),
                        descriptor_dir=path.parent,
                        seeded=seeded,
                    )
                except _BoundedPolicyRefusal as refusal:
                    raise _BoundedPolicyRefusal(str(refusal), where) from refusal
        elif (
            definition is None or definition.bounded_execution_profile.strategy is BoundedExecutionStrategy.UNSUPPORTED
        ):
            raise _BoundedPolicyRefusal("Included descriptor has no proven bounded execution policy", where)
        if tag == "generate" or tag == "iterate":
            name = node.get("name")
            if name is None or "{" in name or name in products:
                raise _BoundedPolicyRefusal("Included products require distinct capture identities", where)
            products.add(name)
            lineage = (*lineage, name)
            # Run-wide producer facts: one statement tree alone cannot see what another step writes.
            entity = resolve_target_entity(node.get("targetEntity"), node.get("type"), name)
            for source_id in sorted(parse_consumer(node.get("target")) & memstores):
                producers.append(
                    _MemstoreProducer(
                        source_id=source_id, entity=entity, product=capture_product_name(NAME_SEPARATOR.join(lineage))
                    )
                )
        for child in node:
            check(child, document, lineage, uri)

    for uri, document in zip((None, *step_uris), documents, strict=True):
        check(document, document, (), uri)
    return memstores, tuple(producers)


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
    includes_validated: bool = False,
    included_memstores: set[str] | None = None,
    graph_producers: tuple[_MemstoreProducer, ...] | None = None,
) -> None:
    """Statement transformer: cap counts, keep only memstore targets, force 1 process.
    When a collector dict is given, the FILE targets removed from each product are
    recorded so smoke_export can replay the captured rows through them afterwards."""
    from datamimic_ce.engine.dsl.api import (
        CompositeStatement,
        DatabaseStatement,
        ExecuteStatement,
        GenerateStatement,
        MongoDBStatement,
        SetupStatement,
    )
    from datamimic_ce.engine.io.api import resolve_target_entity

    assert isinstance(root_stmt, SetupStatement)
    executes, has_include = _dry_run_hazards(root_stmt, includes_validated=includes_validated)
    if has_include:
        raise _BoundedPolicyRefusal("bounded execution refuses unresolved include side effects")
    if not allow_side_effects and descriptor_dir is not None:
        for execute in executes:
            assert isinstance(execute, ExecuteStatement)
            _refuse_unbounded_execute(
                execute.type,
                target=execute.target,
                script=execute.script,
                uri=execute.uri,
                inline=execute.code,
                setup_level=any(execute is child for child in root_stmt.sub_statements),
                descriptor_dir=descriptor_dir,
                seeded=root_stmt.rng_seed is not None,
            )
    elif not allow_side_effects and executes:
        raise _BoundedPolicyRefusal("bounded execution refuses execute without a descriptor directory")
    memstores = _memstore_ids(root_stmt) | (included_memstores or set())
    # With steps, producers come from the whole graph: a step may read what another step wrote.
    memstore_producers = graph_producers if graph_producers is not None else _memstore_producers(root_stmt, memstores)
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
            # Check final rows, including time-series expansion, before runtime planning.
            stmt.bounded_count_limit = max_count
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
                unresolved_includes=bool(included_memstores) and graph_producers is None,
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
            # Only a generate without a source can be fixed by its count; a source's row count stays unproven.
            reason = (
                "runtime cardinality is not statically known; give the generate a literal count, a count "
                "expression over the rows it produces, minCount/maxCount, or a finite source"
                if stmt.source is None
                else "runtime cardinality is not statically known"
            )

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
                if stmt.source is None:
                    # The expression is evaluated per invocation; the runtime guard refuses a value above
                    # max_count, so a run that completes produced every requested row.
                    stmt.bounded_count_limit = max_count
                    bounded_without_cap = True
                    reason = "dynamic count was evaluated at runtime within the per-invocation limit"
                else:
                    # A source may end before the evaluated count, so only the replaced count is provable.
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
                if name in product_budgets:
                    raise _BoundedPolicyRefusal("Included products require distinct canonical capture identities")
                requested_per_parent: int | None = requested
                if (
                    requested_per_parent is None
                    and range_bound is None
                    and count_kind is not _CountBoundaryKind.DYNAMIC
                ):
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


_CapturedRows = dict[NonEmptyStrictStr, tuple[dict[StrictStr, CaptureValue], ...]]
_CAPTURE_ROWS = TypeAdapter(
    dict[NonEmptyStrictStr, list[dict[StrictStr, CaptureValue]] | tuple[dict[StrictStr, CaptureValue], ...]]
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
        CapturedObjectId,
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
        errors.MissingSourceError,
        errors.MissingMemstoreProductError,
        errors.RuleEvaluationError,
        errors.ExportConfigError,
        errors.ExternalFailureCause,
        errors.IncludeError,
        errors.MissingIncludeError,
        errors.GeneratorConfigError,
        errors.ConditionEvaluationError,
        errors.ParserValidationError,
        errors.MissingDescriptorError,
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
        # C code that meets a refused audit event (bounded containment) may surface only this.
        SystemError,
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


def _project_capture_object_ids(value: object) -> object:
    """Copy bounded capture containers, projecting only native BSON identifiers."""
    remaining = MAX_CAPTURE_ITEMS
    ancestors: set[int] = set()

    def project(current: object, depth: int) -> object:
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > MAX_CAPTURE_DEPTH:
            raise ValueError("capture exceeds its item or depth budget")
        if type(current) is ObjectId:
            return CapturedObjectId(value=str(current))
        if not isinstance(current, dict | list | tuple):
            return current
        identity = id(current)
        if identity in ancestors:
            raise ValueError("capture contains a cyclic container")
        if len(current) > remaining:
            raise ValueError("capture exceeds its item budget")
        ancestors.add(identity)
        try:
            if isinstance(current, dict):
                if not all(isinstance(key, str) for key in current):
                    raise ValueError("capture object keys must be strings")
                return {key: project(item, depth + 1) for key, item in current.items()}
            if isinstance(current, tuple):
                return tuple(project(item, depth + 1) for item in current)
            return [project(item, depth + 1) for item in current]
        finally:
            ancestors.remove(identity)

    return project(value, 0)


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
        message.captured,
        tuple(validated_budgets),
        message.smoke_diagnostics,
        message.smoke_export,
        message.source_accesses,
        message.read_files,
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
            expected = {
                _MemstoreBindingStatus.MISSING: 0,
                _MemstoreBindingStatus.RESOLVED: 1,
                _MemstoreBindingStatus.UNRESOLVED_INCLUDES: 0,
            }
            if binding.status in expected and len(binding.producers) != expected[binding.status]:
                raise ValueError("invalid memstore provenance cardinality")
            if binding.status is _MemstoreBindingStatus.AMBIGUOUS and len(binding.producers) < 2:
                raise ValueError("ambiguous memstore provenance needs multiple producers")
            if any(
                producer.product not in budgets or producer.source_id != binding.source_id
                for producer in binding.producers
            ):
                raise ValueError("invalid memstore producer provenance")
    if max_count is not None and sum(len(rows) for rows in message.captured.values()) > max_count:
        raise ValueError("capture rows exceed the shared total Build limit")
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


def _export_capture_value(value: CaptureValue) -> object:
    """Restore native exporter inputs only after the complete capture is validated."""
    if isinstance(value, CapturedObjectId):
        return ObjectId(value.value)
    if isinstance(value, dict):
        return {key: _export_capture_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_export_capture_value(item) for item in value)
    if isinstance(value, list):
        return [_export_capture_value(item) for item in value]
    return value


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
                rows = [
                    {key: _export_capture_value(value) for key, value in row.items()}
                    for row in captured.get(capture_product_name(full_name), ())
                ]
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

        from datamimic_ce.engine.io.api import SourceAccessCapture
        from datamimic_ce.engine.runtime.api import create_run_session
        from datamimic_ce.engine.runtime.contracts import RunRequest

        budgets: _ProductBudgets = {}
        stripped: _StrippedTargets | None = {} if smoke_export else None
        try:
            included_memstores, graph_producers = _validate_bounded_includes(
                path, allow_side_effects=allow_side_effects
            )
            transformer = partial(
                neutralize_for_dry_run,
                max_count=max_count,
                allow_side_effects=allow_side_effects,
                stripped_file_targets=stripped,
                product_budgets=budgets,
                descriptor_dir=path.parent,
                workspace_root=workspace_root,
                includes_validated=True,
                included_memstores=included_memstores,
                graph_producers=graph_producers,
            )
            session = create_run_session(
                RunRequest(
                    descriptor_path=path,
                    task_id=f"dryrun_{uuid.uuid4().hex}",
                    test_mode=True,
                    profile_loader=profile_loader,
                    platform_props=environment_properties,
                    statement_transformer=transformer,
                    included_statement_transformer=transformer,
                    total_row_limit=max_count,
                ),
            )
            with SourceAccessCapture() as source_accesses:
                session.execute()
            capture = session.capture_test_result()
            raw_capture = _validated_capture_rows(_project_capture_object_ids(capture if capture is not None else {}))
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
                source_accesses=source_accesses.snapshot(),
            )
        except Exception as err:
            if is_user_error(err):
                from datamimic_ce.engine.io.api import (
                    normalize_error_cause_for_transport,
                    normalize_exporter_error_cause_for_transport,
                )

                normalize_exporter_error_cause_for_transport(err)
                normalize_error_cause_for_transport(err)
            if isinstance(err, DomainError) and not isinstance(err.__cause__, ExternalFailureCause):
                # Private IPC carries cause types; ordinary Python callers retain native causes.
                cause_types: list[str] = []
                current = err.__cause__
                seen: set[int] = set()
                while current is not None and id(current) not in seen and len(cause_types) < 16:
                    seen.add(id(current))
                    cause_types.append(f"{type(current).__module__}.{type(current).__name__}")
                    current = current.__cause__
                if cause_types:
                    object.__setattr__(err, "__cause__", ExternalFailureCause(cause_types[0], tuple(cause_types)))
            # The process is the untyped runtime boundary: every engine exception must
            # become a stable DM002 response rather than killing the authoring transport.
            message = _WorkerFailure(
                message=str(err) or type(err).__name__,
                fix_hint=_runtime_hint(err),
                error=err if is_user_error(err) else None,
                policy_refusal=isinstance(err, _BoundedPolicyRefusal),
                policy_path=err.path if isinstance(err, _BoundedPolicyRefusal) else (),
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
    limit = max_count
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
        budget.count_kind is not _CountBoundaryKind.DYNAMIC
        and budget.source_exhaustible
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
        if binding.status is _MemstoreBindingStatus.UNRESOLVED_INCLUDES:
            return _unknown_from(base, "XML include graph has no complete run-wide memstore producer proof")
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
        if isinstance(message.error, GeneratorConfigError):
            reason = message.error.constructor_reason
            if reason is not None and (
                type(reason) is not str
                or not reason.strip()
                or message.error.code is not ErrorCode.GENERATOR_CONFIG
                or message.error.issue_code is not None
            ):
                raise ValueError("worker constructor reason has invalid content or identity")
        return message
    raise ValueError("worker returned an unknown envelope")
