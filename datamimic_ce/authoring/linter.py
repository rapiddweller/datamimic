# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Two-phase DSL linter.

Phase 1 walks the lxml tree with all registered rules and AGGREGATES diagnostics
(the engine is fail-fast and reports only the first error). Phase 2 runs the
engine's own parser as authority — but only when phase 1 is error-free, since it
would just re-report the first phase-1 finding in engine wording.
"""

import tempfile
from pathlib import Path

from lxml import etree

from datamimic_ce.authoring.diagnostics import Diagnostic, LintResult
from datamimic_ce.authoring.engine_check import run_engine_parse
from datamimic_ce.authoring.rule_catalog import RuleSeverity
from datamimic_ce.authoring.rules import ALL_RULES, LintContext
from datamimic_ce.authoring.schema import build_schema_index
from datamimic_ce.authoring.xml_loader import load_file, load_source

_INLINE_NOTE = (
    " (inline XML runs in a temp dir: relative source/include paths are not resolvable — "
    "lint the file on disk for those)"
)


def _run_rules(root: etree._Element, base_dir: Path | None) -> list[Diagnostic]:
    ctx = LintContext(root, build_schema_index(), base_dir=base_dir)
    diagnostics: list[Diagnostic] = []
    for rule_cls in ALL_RULES:
        diagnostics.extend(rule_cls().check(ctx))
    diagnostics.sort(key=lambda d: (d.line or 0, d.path, d.rule))
    return diagnostics


def _has_errors(diagnostics: list[Diagnostic]) -> bool:
    return any(d.severity is RuleSeverity.ERROR for d in diagnostics)


def lint_descriptor(path: Path, *, max_diagnostics: int | None = None) -> LintResult:
    """Lint a descriptor file on disk (source/include paths resolve against its dir)."""
    root, load_error = load_file(path)
    if root is None:
        return LintResult.from_diagnostics(
            [load_error] if load_error else [], file=str(path), max_diagnostics=max_diagnostics
        )
    diagnostics = _run_rules(root, base_dir=path.parent)
    if not _has_errors(diagnostics):
        engine_diag = run_engine_parse(path)
        if engine_diag is not None:
            diagnostics.append(engine_diag)
    return LintResult.from_diagnostics(diagnostics, file=str(path), max_diagnostics=max_diagnostics)


def lint_source(xml: str, *, max_diagnostics: int | None = None) -> LintResult:
    """Lint inline descriptor XML (the MCP path). Engine phase runs in a temp dir."""
    root, load_error = load_source(xml)
    if root is None:
        return LintResult.from_diagnostics([load_error] if load_error else [], max_diagnostics=max_diagnostics)
    diagnostics = _run_rules(root, base_dir=None)
    if not _has_errors(diagnostics):
        with tempfile.TemporaryDirectory(prefix="datamimic_lint_") as tmp:
            descriptor = Path(tmp) / "datamimic.xml"
            descriptor.write_text(xml, encoding="utf-8")
            engine_diag = run_engine_parse(descriptor)
        if engine_diag is not None:
            engine_diag.message += _INLINE_NOTE
            diagnostics.append(engine_diag)
    return LintResult.from_diagnostics(diagnostics, max_diagnostics=max_diagnostics)
