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
    (
        "have undefined",
        "A script references a name that is not a field or <variable> in scope. Define a "
        "<variable name=...> first, or use a field that exists on the record.",
    ),
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


def neutralize_for_dry_run(root_stmt: object, *, max_count: int, allow_side_effects: bool) -> None:
    """Statement transformer: cap counts, keep only memstore targets, force 1 process."""
    from datamimic_ce.statements.composite_statement import CompositeStatement
    from datamimic_ce.statements.generate_statement import GenerateStatement
    from datamimic_ce.statements.setup_statement import SetupStatement

    assert isinstance(root_stmt, SetupStatement)
    memstores = _memstore_ids(root_stmt)
    root_stmt.num_process = 1

    def _neutralize(stmt: object, top_level: bool) -> None:
        if isinstance(stmt, GenerateStatement):
            if not allow_side_effects:
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


def dry_run(
    path: Path,
    *,
    max_count: int = 10,
    sample_rows: int = 5,
    allow_side_effects: bool = False,
    timeout_seconds: int = 30,
) -> DryRunResult:
    """Lint first (errors stop before execution), then execute neutralized and capture."""
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
    )


def dry_run_source(
    xml: str,
    *,
    max_count: int = 10,
    sample_rows: int = 5,
    allow_side_effects: bool = False,
    timeout_seconds: int = 30,
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
        )


def _clip_value(value: object, max_chars: int = 200) -> object:
    if not isinstance(value, str):
        return value if isinstance(value, int | float | bool | type(None)) else str(value)
    return value if len(value) <= max_chars else value[: max_chars - 1] + "…"


def _execute(
    path: Path,
    *,
    max_count: int,
    sample_rows: int,
    allow_side_effects: bool,
    timeout_seconds: int,
    lint: LintResult,
) -> DryRunResult:
    from functools import partial

    from datamimic_ce.datamimic import DataMimic
    from datamimic_ce.parsers.descriptor_parser import DescriptorParser

    # Refusal gate: <execute> runs arbitrary SQL/scripts — never silently in a dry-run.
    if not allow_side_effects and _contains_execute(DescriptorParser.parse(path, None)):
        return _run_error(
            RULE_SIDE_EFFECT_REFUSAL,
            "Descriptor contains <execute> (arbitrary SQL/script) — refusing the dry-run.",
            "Re-run with allow_side_effects=true if the statement is safe to execute.",
            lint,
            element="execute",
        )

    engine = DataMimic(
        descriptor_path=path,
        task_id=f"dryrun_{uuid.uuid4().hex}",
        test_mode=True,
        statement_transformer=partial(
            neutralize_for_dry_run, max_count=max_count, allow_side_effects=allow_side_effects
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
    return DryRunResult(
        ok=True,
        stage="run",
        timing_ms=timing_ms,
        products=products[:_MAX_PRODUCTS],
        products_truncated=max(0, len(products) - _MAX_PRODUCTS),
        lint=lint,
    )
