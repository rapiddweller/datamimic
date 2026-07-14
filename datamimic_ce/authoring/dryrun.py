# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Safe, bounded dry-run execution with neutralized targets and typed evidence.

Safety model (allow_side_effects=False, the default):
- memstore targets are KEPT (in-memory, required for pipeline semantics —
  downstream <generate source="mem"> reads them)
- every other target is stripped: file exporters (no output/ artifacts),
  client targets (no DB writes), ConsoleExporter (writes stdout — would corrupt
  a stdio MCP transport) and LogExporter
- <execute> statements (arbitrary SQL/scripts) refuse the run with DM003
- DB/Mongo SOURCES stay allowed — they are reads; connectivity errors surface
  as DM002 with a hint at the conf/{env}.env.properties convention

Every ``<generate>`` invocation is bounded by ``max_count``, including nested,
dynamic-count, ranged-count, and source-driven statements.  A child process is
the cancellation boundary: timeout terminates and reaps it, so user scripts or
runtime I/O cannot continue after the authoring request returns.  Captured rows
and their completeness evidence come from that single engine execution.

smoke_export (opt-in) closes the export-layer gap: stripping file targets also
hides crashes that only happen at write time (e.g. a value the JSON encoder
rejects). With smoke_export=True the captured rows are pushed through each
FILE exporter that was stripped from that product's targets, writing into a
TemporaryDirectory that vanishes afterwards — no artifacts, no descriptor-dir
writes. ConsoleExporter/LogExporter (stdio safety) and client/DB targets are
never smoked. A failing exporter surfaces as a DM002 diagnostic, not an
exception.
"""

import multiprocessing as mp
import pickle
import tempfile
import time
import uuid
from dataclasses import dataclass
from enum import StrEnum
from multiprocessing.connection import Connection
from pathlib import Path

from datamimic_ce.authoring.contracts import (
    AuthoringStage,
    CaptureStatus,
    ProductCaptureEvidence,
    ProductResult,
    RunResult,
)
from datamimic_ce.authoring.diagnostics import Diagnostic, LintResult, Severity
from datamimic_ce.authoring.linter import lint_descriptor, lint_source

RULE_RUNTIME_ERROR = "DM002"
RULE_SIDE_EFFECT_REFUSAL = "DM003"
RULE_EMPTY_OUTPUT = "DM004"


DryRunProduct = ProductResult
"""Backward-compatible alias for the canonical dry-run product contract."""

DryRunResult = RunResult
"""Backward-compatible alias for the canonical dry-run result contract."""


@dataclass(frozen=True)
class CapturedProduct:
    """All bounded rows captured for one runtime product before projection."""

    name: str
    rows: tuple[object, ...]
    capture: ProductCaptureEvidence | None = None


@dataclass(frozen=True)
class CapturedProducts:
    """Internal acceptance input; unlike ``ProductResult`` this is never sampled."""

    products: tuple[CapturedProduct, ...]
    max_count: int

    def get(self, name: str) -> CapturedProduct | None:
        return next((product for product in self.products if product.name == name), None)


@dataclass(frozen=True)
class CapturedRun:
    """One engine result paired with the complete bounded capture from that run."""

    result: DryRunResult
    captured: CapturedProducts


@dataclass(frozen=True)
class _ProductBudget:
    """Static boundary facts recorded while the runtime statement tree is transformed."""

    name: str
    parent_name: str | None
    requested_per_parent: int | None
    explicit_count: bool
    count_kind: "_CountBoundaryKind"
    source_rows_per_parent: int | None
    source_exhaustible: bool
    memstore_source: "_MemstoreSourceBinding | None"
    source_offset: int
    cyclic: bool
    output_multiplier: int
    bounded_without_cap: bool
    cap_applied: bool
    reason: str


_ProductBudgets = dict[str, _ProductBudget]


class _CountBoundaryKind(StrEnum):
    STATIC = "static"
    DYNAMIC = "dynamic"
    RANGE = "range"
    SOURCE = "source"


@dataclass(frozen=True)
class _MemstoreProducer:
    """One runtime statement that writes a typed entity into a declared memstore."""

    source_id: str
    entity: str
    product: str


class _MemstoreBindingStatus(StrEnum):
    RESOLVED = "resolved"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class _MemstoreSourceBinding:
    """Typed runtime routing fact for one generate reading a memstore entity."""

    source_id: str
    entity: str
    status: _MemstoreBindingStatus
    producers: tuple[_MemstoreProducer, ...]


@dataclass(frozen=True)
class _WorkerSuccess:
    captured: dict[str, tuple[object, ...]]
    budgets: tuple[_ProductBudget, ...]
    smoke_diagnostics: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class _WorkerFailure:
    message: str
    fix_hint: str


_WorkerMessage = _WorkerSuccess | _WorkerFailure
_ChildProcess = mp.context.SpawnProcess


_MAX_PRODUCTS = 20  # generate statements per descriptor are few; a generous cap

# Engine runtime errors are opaque stack traces. Map their stable signatures to
# actionable fix hints so a runtime crash teaches the fix (critical for the agent
# lint->fix loop — a weak model cannot recover from "Dry-run failed: <traceback>").
# (substring in str(err)) -> hint
_SCOPE_HINT = (
    "A script references a name that is not in scope. Inside a nested <generate>/"
    "<nestedKey>, record-local names need this. (this.my_key, this.my_var) — bare names "
    "only resolve at the top level; use parent.field / root.field for enclosing records. "
    "Also check the name is defined earlier and note CSV columns arrive as strings "
    "(cast: int(parent.col))."
)
_RUNTIME_HINTS: tuple[tuple[str, str], ...] = (
    (
        "is empty in memstore",
        "A <generate>/<iterate> reads a memstore product that no earlier statement wrote. "
        "Add a <generate target=\"<memstoreId>\"> whose name matches this type=/sourceType= "
        "and place it BEFORE the reader.",
    ),
    (
        "cannot find data source",
        "source= names an undeclared client/memstore. Declare <memstore id>/<database id>/"
        "<mongodb id> with that id, or point source= at a real data file.",
    ),
    # undefined-name family: the engine now names the identifier (NameError/AttributeError
    # path); "have undefined" is kept for the remaining TypeError structure errors.
    ("is not defined in this scope", _SCOPE_HINT),
    ("cannot find attribute", _SCOPE_HINT),
    ("have undefined", _SCOPE_HINT),
    (
        "file not found",
        "An <include>/source path does not exist relative to the descriptor. Fix the path "
        "or create the file.",
    ),
    (
        "connection",
        "Check DB connectivity and the conf/{environment}.env.properties convention "
        "(keys {system}.{db|mongo}.{attr}).",
    ),
    (
        "Evaluation error",
        "A script/count expression is malformed. count= is digits or {python_expr} (no "
        "'script:' prefix); script= is a plain Python expression.",
    ),
)


def _runtime_hint(err: Exception) -> str:
    text = str(err).lower()
    for signature, hint in _RUNTIME_HINTS:
        if signature.lower() in text:
            return hint
    return "Fix the reported runtime error; lint the descriptor for earlier detection."


def _run_error(
    rule: str, message: str, fix_hint: str, lint: LintResult, *, element: str = "setup"
) -> DryRunResult:
    diag = Diagnostic(
        rule=rule, severity=Severity.ERROR, message=message, fix_hint=fix_hint, element=element, path="/setup"
    )
    return DryRunResult(
        ok=False,
        stage=AuthoringStage.RUN,
        lint=lint,
        diagnostics=[diag],
    )


def _memstore_ids(root_stmt: object) -> set[str]:
    from datamimic_ce.statements.memstore_statement import MemstoreStatement
    from datamimic_ce.statements.setup_statement import SetupStatement

    assert isinstance(root_stmt, SetupStatement)
    return {stmt.id for stmt in root_stmt.sub_statements if isinstance(stmt, MemstoreStatement)}


def _generate_statements(root_stmt: object) -> tuple[object, ...]:
    """Collect generate statements without assuming their lexical or execution order."""

    from datamimic_ce.statements.composite_statement import CompositeStatement
    from datamimic_ce.statements.generate_statement import GenerateStatement
    from datamimic_ce.statements.setup_statement import SetupStatement

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
    from datamimic_ce.statements.generate_statement import GenerateStatement
    from datamimic_ce.statements.statement_util import StatementUtil

    producers: list[_MemstoreProducer] = []
    for statement in _generate_statements(root_stmt):
        if not isinstance(statement, GenerateStatement):
            continue
        entity = StatementUtil.resolve_target_entity(
            statement.target_entity,
            statement.type,
            statement.name,
        )
        for source_id in sorted(statement.targets & memstore_ids):
            producers.append(
                _MemstoreProducer(
                    source_id=source_id,
                    entity=entity,
                    product=_capture_name(statement.full_name),
                )
            )
    return tuple(producers)


def _memstore_source_binding(
    stmt: object,
    *,
    memstore_ids: set[str],
    producers: tuple[_MemstoreProducer, ...],
) -> _MemstoreSourceBinding | None:
    from datamimic_ce.constants.element_constants import EL_GENERATE
    from datamimic_ce.model.constraints import source_file_format_for
    from datamimic_ce.statements.generate_statement import GenerateStatement
    from datamimic_ce.statements.statement_util import StatementUtil

    if not isinstance(stmt, GenerateStatement) or stmt.source not in memstore_ids:
        return None
    if source_file_format_for(EL_GENERATE, stmt.source, stmt.type) is not None:
        return None
    entity = StatementUtil.resolve_source_entity(stmt)
    candidates = tuple(
        producer
        for producer in producers
        if producer.source_id == stmt.source and producer.entity == entity
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


def _contains_execute(root_stmt: object) -> bool:
    from datamimic_ce.statements.composite_statement import CompositeStatement
    from datamimic_ce.statements.execute_statement import ExecuteStatement

    def _walk(stmt: object) -> bool:
        if isinstance(stmt, ExecuteStatement):
            return True
        if isinstance(stmt, CompositeStatement):
            return any(_walk(sub) for sub in stmt.sub_statements)
        return False

    return _walk(root_stmt)


# One stripped file target of a product: (exporter name in the registry, ctor params).
_FileTarget = tuple[str, dict[str, object]]
# product full_name -> (file basename, its stripped file targets)
_StrippedTargets = dict[str, tuple[str, list[_FileTarget]]]


def _capture_name(full_name: str) -> str:
    """Use the exact nested-product key used by ``TestResultExporter``."""

    from datamimic_ce.constants.convention_constants import NAME_SEPARATOR

    if NAME_SEPARATOR in full_name:
        return full_name.split(NAME_SEPARATOR, 1)[-1]
    return full_name


def _parent_capture_name(stmt: object) -> str | None:
    from datamimic_ce.statements.generate_statement import GenerateStatement
    from datamimic_ce.statements.statement import Statement

    if not isinstance(stmt, Statement):
        return None
    parent = stmt.parent_stmt
    while parent is not None and not isinstance(parent, GenerateStatement):
        parent = parent.parent_stmt
    return _capture_name(parent.full_name) if isinstance(parent, GenerateStatement) else None


def _source_row_count(
    stmt: object,
    *,
    descriptor_dir: Path | None,
    default_separator: str,
) -> int | None:
    """Return a file source's statically observable remaining rows, if supported."""

    from datamimic_ce.constants.element_constants import EL_GENERATE
    from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry
    from datamimic_ce.model.constraints import SourceFileFormat, source_file_format_for
    from datamimic_ce.statements.generate_statement import GenerateStatement

    if not isinstance(stmt, GenerateStatement) or descriptor_dir is None or stmt.source is None:
        return None
    source_format = source_file_format_for(EL_GENERATE, stmt.source, stmt.type)
    if source_format is None or source_format is SourceFileFormat.DBUNIT_XML:
        return None
    try:
        rows = DataSourceRegistry._get_source(
            str(descriptor_dir / stmt.source),
            stmt.separator or default_separator,
            source_format,
        )
    except Exception:
        # This is evidence discovery, not execution. The canonical runtime reports
        # the real file error; failure to prove a length must remain UNKNOWN.
        return None
    return max(0, len(rows) - stmt.offset)


def _range_upper_bound(stmt: object) -> int | None:
    from datamimic_ce.statements.generate_statement import GenerateStatement

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
    from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS, ExporterUtil

    parsed: list[_FileTarget] = []
    for raw in sorted(targets):
        try:
            entries = ExporterUtil.parse_function_string(raw)
        except ValueError:
            continue  # malformed target string — the engine's own path reports it
        for entry in entries:
            if entry["function_name"] in _BUFFERED_EXPORTERS:
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
) -> None:
    """Statement transformer: cap counts, keep only memstore targets, force 1 process.
    When a collector dict is given, the FILE targets removed from each product are
    recorded so smoke_export can replay the captured rows through them afterwards."""
    from datamimic_ce.statements.composite_statement import CompositeStatement
    from datamimic_ce.statements.generate_statement import GenerateStatement
    from datamimic_ce.statements.setup_statement import SetupStatement
    from datamimic_ce.statements.statement_util import StatementUtil

    assert isinstance(root_stmt, SetupStatement)
    memstores = _memstore_ids(root_stmt)
    memstore_producers = _memstore_producers(root_stmt, memstores)
    root_stmt.num_process = 1

    default_separator = root_stmt.default_separator or "|"

    def _neutralize(stmt: object) -> None:
        if isinstance(stmt, GenerateStatement):
            if not allow_side_effects:
                if stripped_file_targets is not None:
                    file_targets = _parse_buffered_targets(stmt.targets - memstores)
                    if file_targets:
                        # same basename resolution as the real exporter factory
                        basename = StatementUtil.resolve_target_entity(stmt.target_entity, None, stmt.name)
                        stripped_file_targets[stmt.full_name] = (basename, file_targets)
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
            from datamimic_ce.enums.distribution_enums import SourceDistribution

            source_exhaustible = (
                source_rows is not None
                and not stmt.cyclic
                and stmt.distribution is not SourceDistribution.CUMULATED
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
                name = _capture_name(stmt.full_name)
                product_budgets[name] = _ProductBudget(
                    name=name,
                    parent_name=_parent_capture_name(stmt),
                    requested_per_parent=(
                        requested
                        if requested is not None
                        else source_rows if range_bound is None else None
                    ),
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


def _smoke_setup_context(tmp_dir: Path):
    """Minimal engine context for smoke writes: every value an exporter reads from it
    is a default; descriptor_dir points at the throwaway tmp dir so buffer files can
    never land next to the real descriptor."""
    from datamimic_ce.contexts.setup_context import SetupContext
    from datamimic_ce.exporters.test_result_exporter import TestResultExporter
    from datamimic_ce.product_storage.memstore_manager import MemstoreManager

    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id=f"smoke_{uuid.uuid4().hex}",
        test_mode=False,
        test_result_exporter=TestResultExporter(),
        default_separator=",",
        default_locale="en_US",
        default_dataset="US",
        use_mp=False,
        descriptor_dir=tmp_dir,
        num_process=1,
        default_variable_prefix="__",
        default_variable_suffix="__",
        default_line_separator=None,
    )


def _smoke_export(captured: dict[str, list[object]], stripped: _StrippedTargets) -> list[Diagnostic]:
    """Replay the captured rows through each stripped file exporter inside a temp dir
    (write + finalize — the two phases where serialization crashes live). The tempdir
    context manager guarantees zero artifacts. Failures become DM002 diagnostics."""
    from datamimic_ce.constants.convention_constants import NAME_SEPARATOR
    from datamimic_ce.exporters.exporter_config import ExporterConfig
    from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
    from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS

    diagnostics: list[Diagnostic] = []
    with tempfile.TemporaryDirectory(prefix="datamimic_smoke_") as tmp:
        smoke_ctx = _smoke_setup_context(Path(tmp))
        for full_name, (basename, file_targets) in sorted(stripped.items()):
            # TestResultExporter stores nested products under the full_name MINUS its
            # first segment ("customers|accounts" -> "accounts") — mirror that here.
            capture_key = full_name.split(NAME_SEPARATOR, 1)[-1] if NAME_SEPARATOR in full_name else full_name
            rows = [row for row in captured.get(capture_key, []) if isinstance(row, dict)]
            if not rows:
                continue
            for exporter_name, params in file_targets:
                try:
                    config = ExporterConfig(
                        setup_context=smoke_ctx,
                        product_name=basename,
                        chunk_size=None,
                        encoding=None,
                        export_uri=None,
                    )
                    exporter = _BUFFERED_EXPORTERS[exporter_name](config, dict(params))
                    exporter.consume((basename, rows), full_name, ExporterStateManager(worker_id=1))
                    exporter.finalize_chunks(1)
                except Exception as err:
                    diagnostics.append(
                        Diagnostic(
                            rule=RULE_RUNTIME_ERROR,
                            severity=Severity.ERROR,
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
                    )
    return diagnostics


def dry_run(
    path: Path,
    *,
    max_count: int = 10,
    sample_rows: int = 5,
    allow_side_effects: bool = False,
    timeout_seconds: int = 30,
    smoke_export: bool = False,
) -> DryRunResult:
    """Lint first (errors stop before execution), then execute neutralized and capture.
    smoke_export additionally replays captured rows through the stripped file exporters
    in a temp dir, catching export-layer crashes the plain dry-run cannot see."""
    return dry_run_captured(
        path,
        max_count=max_count,
        sample_rows=sample_rows,
        allow_side_effects=allow_side_effects,
        timeout_seconds=timeout_seconds,
        smoke_export=smoke_export,
    ).result


def dry_run_captured(
    path: Path,
    *,
    max_count: int = 10,
    sample_rows: int = 5,
    allow_side_effects: bool = False,
    timeout_seconds: int = 30,
    smoke_export: bool = False,
) -> CapturedRun:
    """Canonical file-backed dry-run retaining all bounded rows internally."""

    lint = lint_descriptor(path)
    if not lint.ok:
        result = DryRunResult(
            ok=False,
            stage=AuthoringStage.LINT,
            lint=lint,
            diagnostics=lint.diagnostics,
        )
        return CapturedRun(result=result, captured=CapturedProducts((), max_count))
    return _execute_captured(
        path,
        max_count=max_count,
        sample_rows=sample_rows,
        allow_side_effects=allow_side_effects,
        timeout_seconds=timeout_seconds,
        lint=lint,
        smoke_export=smoke_export,
    )


def dry_run_source(
    xml: str,
    *,
    max_count: int = 10,
    sample_rows: int = 5,
    allow_side_effects: bool = False,
    timeout_seconds: int = 30,
    smoke_export: bool = False,
) -> DryRunResult:
    """Dry-run inline descriptor XML in a temp dir (relative resources not resolvable)."""
    return dry_run_source_captured(
        xml,
        max_count=max_count,
        sample_rows=sample_rows,
        allow_side_effects=allow_side_effects,
        timeout_seconds=timeout_seconds,
        smoke_export=smoke_export,
    ).result


def dry_run_source_captured(
    xml: str,
    *,
    max_count: int = 10,
    sample_rows: int = 5,
    allow_side_effects: bool = False,
    timeout_seconds: int = 30,
    smoke_export: bool = False,
) -> CapturedRun:
    """Canonical inline dry-run retaining acceptance rows before sample projection."""

    lint = lint_source(xml)
    if not lint.ok:
        result = DryRunResult(
            ok=False,
            stage=AuthoringStage.LINT,
            lint=lint,
            diagnostics=lint.diagnostics,
        )
        return CapturedRun(result=result, captured=CapturedProducts((), max_count))
    with tempfile.TemporaryDirectory(prefix="datamimic_dryrun_") as tmp:
        descriptor = Path(tmp) / "datamimic.xml"
        descriptor.write_text(xml, encoding="utf-8")
        return _execute_captured(
            descriptor,
            max_count=max_count,
            sample_rows=sample_rows,
            allow_side_effects=allow_side_effects,
            timeout_seconds=timeout_seconds,
            lint=lint,
            smoke_export=smoke_export,
        )


def _clip_value(value: object, max_chars: int = 200) -> object:
    """Clip strings but PRESERVE dict/list structure. Agents verify intent by inspecting
    the sample ("is reviews a list of objects with a rating?"); stringifying nested
    structures would make that check impossible."""
    if isinstance(value, str):
        return value if len(value) <= max_chars else value[: max_chars - 1] + "…"
    if isinstance(value, int | float | bool | type(None)):
        return value
    if isinstance(value, dict):  # includes DotableDict rows from nestedKey/entity output
        return {str(k): _clip_value(v, max_chars) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_clip_value(v, max_chars) for v in value]
    return str(value)  # datetime, Decimal, custom objects -> readable leaf


def _failed_capture(result: DryRunResult, max_count: int) -> CapturedRun:
    return CapturedRun(result=result, captured=CapturedProducts((), max_count))


def _ipc_safe_value(value: object) -> object:
    """Preserve structured values across IPC, stringifying only unpicklable leaves."""

    if isinstance(value, str | bytes | int | float | bool | type(None)):
        return value
    if isinstance(value, dict):
        return {str(key): _ipc_safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_ipc_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_ipc_safe_value(item) for item in value)
    try:
        pickle.dumps(value)
    except (pickle.PickleError, TypeError, AttributeError):
        return str(value)
    return value


def _engine_process_worker(
    path: Path,
    max_count: int,
    allow_side_effects: bool,
    smoke_export: bool,
    send_connection: Connection,
) -> None:
    """Execute and capture exactly one engine run inside the cancellable process."""

    from functools import partial

    from datamimic_ce.datamimic import DataMimic

    budgets: _ProductBudgets = {}
    stripped: _StrippedTargets | None = {} if smoke_export else None
    try:
        engine = DataMimic(
            descriptor_path=path,
            task_id=f"dryrun_{uuid.uuid4().hex}",
            test_mode=True,
            statement_transformer=partial(
                neutralize_for_dry_run,
                max_count=max_count,
                allow_side_effects=allow_side_effects,
                stripped_file_targets=stripped,
                product_budgets=budgets,
                descriptor_dir=path.parent,
            ),
        )
        engine.parse_and_execute()
        raw_capture = engine.capture_test_result() or {}
        smoke_diagnostics = _smoke_export(raw_capture, stripped) if stripped else []
        captured = {
            str(name): tuple(_ipc_safe_value(row) for row in rows)
            for name, rows in raw_capture.items()
        }
        message: _WorkerMessage = _WorkerSuccess(
            captured=captured,
            budgets=tuple(sorted(budgets.values(), key=lambda budget: budget.name)),
            smoke_diagnostics=tuple(
                diagnostic.model_dump(mode="json") for diagnostic in smoke_diagnostics
            ),
        )
    except Exception as err:
        # The process is the untyped runtime boundary: every engine exception must
        # become a stable DM002 response rather than killing the authoring transport.
        message = _WorkerFailure(message=str(err), fix_hint=_runtime_hint(err))
    try:
        send_connection.send(message)
    finally:
        send_connection.close()


def _process_context() -> mp.context.SpawnContext:
    """Use one deterministic cross-platform start strategy for threaded transports."""

    return mp.context.SpawnContext()


def _terminate_and_reap(process: _ChildProcess) -> None:
    """Stop a timed-out child and synchronously reap it; never leave a zombie."""

    if not process.is_alive():
        process.join(timeout=0.1)
        return
    process.terminate()
    process.join(timeout=0.2)
    if process.is_alive():
        process.kill()
        process.join(timeout=0.2)


def _receive_worker_message(
    receive_connection: Connection,
    process: _ChildProcess,
    timeout_seconds: int,
) -> _WorkerMessage | None:
    deadline = time.monotonic() + timeout_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        if receive_connection.poll(min(0.05, remaining)):
            try:
                message = receive_connection.recv()
            except (EOFError, OSError):
                return _WorkerFailure(
                    message="dry-run worker exited without a result",
                    fix_hint="Inspect the descriptor for a native runtime crash.",
                )
            if isinstance(message, _WorkerSuccess | _WorkerFailure):
                return message
            return _WorkerFailure(
                message="dry-run worker returned an invalid result",
                fix_hint="Report this authoring runtime protocol error.",
            )
        if not process.is_alive():
            return _WorkerFailure(
                message=f"dry-run worker exited with code {process.exitcode}",
                fix_hint="Inspect the descriptor for a native runtime crash.",
            )


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
        return base if base.status is CaptureStatus.CAPPED else _unknown_from(
            base,
            "dynamic count replacement prevents a complete memstore-read proof",
        )
    if budget.cyclic:
        return _unknown_from(
            base,
            "cyclic memstore reads do not provide finite exhaustion evidence",
        )
    if budget.count_kind is _CountBoundaryKind.SOURCE:
        if available > base.limit:
            if base.observed == base.limit:
                return ProductCaptureEvidence(
                    status=CaptureStatus.CAPPED,
                    requested=available,
                    observed=base.observed,
                    limit=base.limit,
                    reason=(
                        f"finite memstore source has {available} available rows, "
                        f"above capture limit {base.limit}"
                    ),
                )
            return _unknown_from(base, "memstore source did not reach its proven finite window")
        if base.observed == available:
            return ProductCaptureEvidence(
                status=CaptureStatus.EXHAUSTED,
                requested=available,
                observed=base.observed,
                limit=base.limit,
                reason=(
                    f"uniquely resolved memstore producer was fully read: "
                    f"{available} finite rows"
                ),
            )
        return _unknown_from(base, "memstore source did not exhaust its proven finite window")
    if budget.count_kind is _CountBoundaryKind.STATIC and base.requested is not None:
        effective_requested = min(base.requested, available)
        if base.observed == effective_requested:
            if base.requested >= available:
                return ProductCaptureEvidence(
                    status=CaptureStatus.EXHAUSTED,
                    requested=base.requested,
                    observed=base.observed,
                    limit=base.limit,
                    reason=(
                        f"static request reached all {available} rows of the uniquely "
                        "resolved memstore producer"
                    ),
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
    captured: dict[str, tuple[object, ...]],
    *,
    max_count: int,
) -> dict[str, ProductCaptureEvidence]:
    """Resolve ancestry and memstore provenance recursively, independent of name order."""

    observed_by_name = {name: len(rows) for name, rows in captured.items()}
    resolved: dict[str, ProductCaptureEvidence] = {}
    visiting: set[str] = set()

    def _resolve(name: str) -> ProductCaptureEvidence:
        existing = resolved.get(name)
        if existing is not None:
            return existing
        budget = budgets.get(name)
        observed = observed_by_name.get(name, 0)
        base = _capture_evidence(
            budget,
            observed=observed,
            max_count=max_count,
            observed_by_name=observed_by_name,
        )
        if name in visiting:
            return _unknown_from(base, "capture dependency cycle prevents a completeness proof")
        visiting.add(name)
        evidence = base
        dependency_blocked = False
        if budget is not None and budget.parent_name is not None:
            if budget.parent_name not in observed_by_name:
                evidence = _unknown_from(base, "parent product is missing from runtime capture")
                dependency_blocked = True
            else:
                parent_evidence = _resolve(budget.parent_name)
                if not parent_evidence.complete:
                    evidence = _unknown_from(
                        base,
                        "parent product capture is not proven complete",
                    )
                    dependency_blocked = True
        binding = budget.memstore_source if budget is not None else None
        if budget is not None and binding is not None and not dependency_blocked:
            if binding.status is _MemstoreBindingStatus.MISSING:
                evidence = _unknown_from(
                    base,
                    (
                        f"memstore '{binding.source_id}' entity '{binding.entity}' "
                        "has no captured producer"
                    ),
                )
            elif binding.status is _MemstoreBindingStatus.AMBIGUOUS:
                evidence = _unknown_from(
                    base,
                    (
                        f"memstore '{binding.source_id}' entity '{binding.entity}' "
                        "has multiple possible producers"
                    ),
                )
            else:
                producer = next(iter(binding.producers), None)
                if producer is None or producer.product not in observed_by_name:
                    evidence = _unknown_from(
                        base,
                        "resolved memstore producer is missing from runtime capture",
                    )
                else:
                    evidence = _memstore_capture_evidence(
                        budget,
                        base,
                        producer_evidence=_resolve(producer.product),
                        producer_observed=observed_by_name[producer.product],
                        parent_observed=(
                            observed_by_name.get(budget.parent_name, 0)
                            if budget.parent_name is not None
                            else 1
                        ),
                    )
        visiting.remove(name)
        resolved[name] = evidence
        return evidence

    for product_name in captured:
        _resolve(product_name)
    return resolved


def _execute_captured(
    path: Path,
    *,
    max_count: int,
    sample_rows: int,
    allow_side_effects: bool,
    timeout_seconds: int,
    lint: LintResult,
    smoke_export: bool = False,
) -> CapturedRun:
    from datamimic_ce.parsers.descriptor_parser import DescriptorParser

    # Refusal gate: <execute> runs arbitrary SQL/scripts — never silently in a dry-run.
    # The parse can raise (e.g. lint suppressed a credential error) — map it to DM002,
    # never let it crash the tool.
    try:
        has_execute = _contains_execute(DescriptorParser.parse(path, None))
    except Exception as err:
        return _failed_capture(
            _run_error(RULE_RUNTIME_ERROR, f"Dry-run failed: {err}", _runtime_hint(err), lint),
            max_count,
        )
    if not allow_side_effects and has_execute:
        return _failed_capture(
            _run_error(
                RULE_SIDE_EFFECT_REFUSAL,
                "Descriptor contains <execute> (arbitrary SQL/script) — refusing the dry-run.",
                "Re-run with allow_side_effects=true if the statement is safe to execute.",
                lint,
                element="execute",
            ),
            max_count,
        )

    started = time.perf_counter()
    context = _process_context()
    receive_connection, send_connection = context.Pipe(duplex=False)
    process = context.Process(
        target=_engine_process_worker,
        args=(path, max_count, allow_side_effects, smoke_export, send_connection),
        name="datamimic-authoring-dryrun",
    )
    try:
        process.start()
    except (OSError, RuntimeError) as err:
        receive_connection.close()
        send_connection.close()
        return _failed_capture(
            _run_error(
                RULE_RUNTIME_ERROR,
                f"Dry-run worker could not start: {err}",
                "Check the local multiprocessing runtime and retry.",
                lint,
            ),
            max_count,
        )
    send_connection.close()
    try:
        message = _receive_worker_message(receive_connection, process, timeout_seconds)
    finally:
        receive_connection.close()
    if message is None:
        _terminate_and_reap(process)
        return _failed_capture(
            _run_error(
                RULE_RUNTIME_ERROR,
                f"Dry-run exceeded {timeout_seconds}s and was terminated.",
                "Reduce counts/pageSize or raise timeout_seconds; inspect slow scripts and sources.",
                lint,
            ),
            max_count,
        )
    process.join(timeout=0.2)
    if process.is_alive():
        _terminate_and_reap(process)
    if isinstance(message, _WorkerFailure):
        return _failed_capture(
            _run_error(
                RULE_RUNTIME_ERROR,
                f"Dry-run failed: {message.message}",
                message.fix_hint,
                lint,
            ),
            max_count,
        )
    timing_ms = int((time.perf_counter() - started) * 1000)

    captured = message.captured
    budgets = {budget.name: budget for budget in message.budgets}
    smoke_diags = [
        Diagnostic.model_validate(diagnostic) for diagnostic in message.smoke_diagnostics
    ]
    evidence_by_name = _capture_evidence_by_product(
        budgets,
        captured,
        max_count=max_count,
    )
    captured_products = CapturedProducts(
        products=tuple(
            CapturedProduct(
                name=str(name),
                rows=tuple(rows),
                capture=evidence_by_name[str(name)],
            )
            for name, rows in sorted(captured.items())
        ),
        max_count=max_count,
    )
    products: list[DryRunProduct] = []
    for product in captured_products.products:
        name = product.name
        rows = product.rows
        capture = product.capture
        if capture is None:
            capture = evidence_by_name[name]
        sample = [
            {str(k): _clip_value(v) for k, v in row.items()} if isinstance(row, dict) else {"value": _clip_value(row)}
            for row in rows[:sample_rows]
        ]
        products.append(
            DryRunProduct(
                name=name,
                count=len(rows),
                sample=sample,
                truncated_rows=len(rows) > sample_rows,
                capture=capture,
            )
        )
    products.sort(key=lambda p: p.name)
    # A descriptor that generates nothing at all almost always means the author's
    # intent didn't take (empty <setup>, missing/zero counts, a mis-shaped tree).
    # Neither lint nor a crash catches it — surface it as a diagnostic.
    zero_rows: list[Diagnostic] = []
    if sum(p.count for p in products) == 0:
        zero_rows.append(
            Diagnostic(
                rule=RULE_EMPTY_OUTPUT,
                severity=Severity.WARNING,
                message="The dry-run generated 0 rows across all products — the descriptor produces no data.",
                fix_hint="Ensure a <generate> exists with a positive count (or a source that returns rows).",
                element="setup",
                path="/setup",
            )
        )
    result = DryRunResult(
        ok=not smoke_diags and not zero_rows,
        stage=AuthoringStage.RUN,
        timing_ms=timing_ms,
        products=products[:_MAX_PRODUCTS],
        products_truncated=max(0, len(products) - _MAX_PRODUCTS),
        lint=lint,
        diagnostics=[*smoke_diags, *zero_rows],
    )
    return CapturedRun(result=result, captured=captured_products)


def _execute(
    path: Path,
    *,
    max_count: int,
    sample_rows: int,
    allow_side_effects: bool,
    timeout_seconds: int,
    lint: LintResult,
    smoke_export: bool = False,
) -> DryRunResult:
    """Compatibility projection over the one canonical captured execution path."""

    return _execute_captured(
        path,
        max_count=max_count,
        sample_rows=sample_rows,
        allow_side_effects=allow_side_effects,
        timeout_seconds=timeout_seconds,
        lint=lint,
        smoke_export=smoke_export,
    ).result
