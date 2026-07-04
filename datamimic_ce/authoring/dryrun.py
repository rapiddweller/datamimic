# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Safe dry-run of a descriptor: execute with capped counts and neutralized
targets, capture sample rows in memory, never write artifacts or hit stores.

Safety model (allow_side_effects=False, the default):
- memstore targets are KEPT (in-memory, required for pipeline semantics —
  downstream <generate source="mem"> reads them)
- every other target is stripped: file exporters (no output/ artifacts),
  client targets (no DB writes), ConsoleExporter (writes stdout — would corrupt
  a stdio MCP transport) and LogExporter
- <execute> statements (arbitrary SQL/scripts) refuse the run with DM003
- DB/Mongo SOURCES stay allowed — they are reads; connectivity errors surface
  as DM002 with a hint at the conf/{env}.env.properties convention

test_mode capture is target-independent, so rows still arrive with all
targets stripped. Counts: top-level digit counts are capped; source-driven
generates get an explicit capped count (which also bypasses the DB
count_query_length path); {script} counts cannot be capped pre-context and
rely on the timeout.

smoke_export (opt-in) closes the export-layer gap: stripping file targets also
hides crashes that only happen at write time (e.g. a value the JSON encoder
rejects). With smoke_export=True the captured rows are pushed through each
FILE exporter that was stripped from that product's targets, writing into a
TemporaryDirectory that vanishes afterwards — no artifacts, no descriptor-dir
writes. ConsoleExporter/LogExporter (stdio safety) and client/DB targets are
never smoked. A failing exporter surfaces as a DM002 diagnostic, not an
exception.
"""

import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path

from pydantic import BaseModel, Field

from datamimic_ce.authoring.diagnostics import Diagnostic, LintResult, Severity
from datamimic_ce.authoring.linter import lint_descriptor, lint_source

RULE_RUNTIME_ERROR = "DM002"
RULE_SIDE_EFFECT_REFUSAL = "DM003"
RULE_EMPTY_OUTPUT = "DM004"


class DryRunProduct(BaseModel):
    name: str
    count: int
    sample: list[dict[str, object]] = Field(default_factory=list)
    truncated_rows: bool = False


class DryRunResult(BaseModel):
    ok: bool
    stage: str  # "lint" | "run"
    timing_ms: int | None = None
    products: list[DryRunProduct] = Field(default_factory=list)
    products_truncated: int = 0
    lint: LintResult | None = None
    diagnostics: list[Diagnostic] = Field(default_factory=list)


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
    return DryRunResult(ok=False, stage="run", lint=lint, diagnostics=[diag])


def _memstore_ids(root_stmt: object) -> set[str]:
    from datamimic_ce.statements.memstore_statement import MemstoreStatement
    from datamimic_ce.statements.setup_statement import SetupStatement

    assert isinstance(root_stmt, SetupStatement)
    return {stmt.id for stmt in root_stmt.sub_statements if isinstance(stmt, MemstoreStatement)}


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
    root_stmt.num_process = 1

    def _neutralize(stmt: object, top_level: bool) -> None:
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
            if top_level:
                count = stmt.count
                if count is None or (isinstance(count, str) and count.isdigit() and int(count) > max_count):
                    # explicit count also short-circuits source-length resolution
                    # (incl. the DB count_query_length path)
                    stmt.count = str(max_count)
        if isinstance(stmt, CompositeStatement):
            for sub in stmt.sub_statements:
                _neutralize(sub, top_level=False)

    for stmt in root_stmt.sub_statements:
        _neutralize(stmt, top_level=True)


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
    lint = lint_descriptor(path)
    if not lint.ok:
        return DryRunResult(ok=False, stage="lint", lint=lint, diagnostics=lint.diagnostics)
    return _execute(
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
    lint = lint_source(xml)
    if not lint.ok:
        return DryRunResult(ok=False, stage="lint", lint=lint, diagnostics=lint.diagnostics)
    with tempfile.TemporaryDirectory(prefix="datamimic_dryrun_") as tmp:
        descriptor = Path(tmp) / "datamimic.xml"
        descriptor.write_text(xml, encoding="utf-8")
        return _execute(
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
    from functools import partial

    from datamimic_ce.datamimic import DataMimic
    from datamimic_ce.parsers.descriptor_parser import DescriptorParser

    # Refusal gate: <execute> runs arbitrary SQL/scripts — never silently in a dry-run.
    # The parse can raise (e.g. lint suppressed a credential error) — map it to DM002,
    # never let it crash the tool.
    try:
        has_execute = _contains_execute(DescriptorParser.parse(path, None))
    except Exception as err:
        return _run_error(RULE_RUNTIME_ERROR, f"Dry-run failed: {err}", _runtime_hint(err), lint)
    if not allow_side_effects and has_execute:
        return _run_error(
            RULE_SIDE_EFFECT_REFUSAL,
            "Descriptor contains <execute> (arbitrary SQL/script) — refusing the dry-run.",
            "Re-run with allow_side_effects=true if the statement is safe to execute.",
            lint,
            element="execute",
        )

    # smoke_export needs to know WHICH file targets were stripped from each product.
    stripped: _StrippedTargets | None = {} if smoke_export else None
    engine = DataMimic(
        descriptor_path=path,
        task_id=f"dryrun_{uuid.uuid4().hex}",
        test_mode=True,
        statement_transformer=partial(
            neutralize_for_dry_run,
            max_count=max_count,
            allow_side_effects=allow_side_effects,
            stripped_file_targets=stripped,
        ),
    )

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(engine.parse_and_execute)
        try:
            future.result(timeout=timeout_seconds)
        except FutureTimeoutError:
            return _run_error(
                RULE_RUNTIME_ERROR,
                f"Dry-run exceeded {timeout_seconds}s and was abandoned.",
                "Reduce counts/pageSize or raise timeout_seconds; check for unbounded {script} counts.",
                lint,
            )
        except Exception as err:  # engine raises plain ValueError/Exception — map to DM002
            return _run_error(RULE_RUNTIME_ERROR, f"Dry-run failed: {err}", _runtime_hint(err), lint)
    timing_ms = int((time.perf_counter() - started) * 1000)

    captured = engine.capture_test_result() or {}
    # Opt-in export smoke: replay captured rows through the stripped file exporters.
    smoke_diags: list[Diagnostic] = []
    if stripped:
        smoke_diags = _smoke_export(captured, stripped)
    products: list[DryRunProduct] = []
    for name, rows in captured.items():
        sample = [
            {str(k): _clip_value(v) for k, v in row.items()} if isinstance(row, dict) else {"value": _clip_value(row)}
            for row in rows[:sample_rows]
        ]
        products.append(
            DryRunProduct(name=name, count=len(rows), sample=sample, truncated_rows=len(rows) > sample_rows)
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
    return DryRunResult(
        ok=not smoke_diags,  # a smoke-export failure means the real run WOULD crash at export
        stage="run",
        timing_ms=timing_ms,
        products=products[:_MAX_PRODUCTS],
        products_truncated=max(0, len(products) - _MAX_PRODUCTS),
        lint=lint,
        diagnostics=[*smoke_diags, *zero_rows],
    )
