# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DM3xx — best-practice rules where the ENGINE STAYS SILENT and does something
surprising. These are the linter's flagship rules: nothing else catches them."""

import re
from collections.abc import Iterable

from datamimic_ce.authoring.diagnostics import Diagnostic, Severity
from datamimic_ce.authoring.rules.base import LintContext, Rule
from datamimic_ce.constants.element_constants import (
    EL_GENERATE,
    EL_ID,
    EL_ITERATE,
    EL_KEY,
    EL_NESTED_KEY,
    EL_REFERENCE,
    EL_VARIABLE,
)

_GENERATES = (EL_GENERATE, EL_ITERATE)
_SOURCE_READERS = (*_GENERATES, EL_VARIABLE, EL_NESTED_KEY, EL_REFERENCE)

# A bare __name__ token (the string-interpolation syntax) used as an identifier —
# not `.__dunder__` attribute access, which is legitimate Python.
_INTERP_TOKEN = re.compile(r"(?<![\w.])__[A-Za-z]\w*__")
# Attributes evaluated as Python expressions, where __var__ interpolation does NOT apply.
_SCRIPT_ATTRS = ("script", "condition")


def _is_true(value: str | None) -> bool:
    return value is not None and value.lower() in ("true", "1")


class DistributionDefaultsToRandom(Rule):
    id = "DM301"
    severity = Severity.WARNING
    docs = "reference://distributions"

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_SOURCE_READERS):
            if element.get("source") is not None and element.get("distribution") is None:
                yield ctx.diag(
                    type(self),
                    element,
                    "Source rows are read in RANDOM order — absent distribution defaults to random, "
                    "not file/table order.",
                    'Add distribution="ordered" for source order, or distribution="random" to make '
                    "the shuffle explicit.",
                )


class NonOrderedLoadsWholeSource(Rule):
    id = "DM302"
    severity = Severity.HINT
    docs = "reference://distributions"

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_SOURCE_READERS):
            if element.get("source") is None:
                continue
            distribution = element.get("distribution")
            if distribution in ("random", "cumulated") or _is_true(element.get("unique")):
                yield ctx.diag(
                    type(self),
                    element,
                    f"distribution='{distribution or 'random'}'"
                    f"{' with unique' if _is_true(element.get('unique')) else ''} loads the ENTIRE "
                    "source into memory before selecting; only 'ordered' reads page by page.",
                    'For large sources use distribution="ordered", or accept the memory cost knowingly.',
                )


class UnseededRunNotReproducible(Rule):
    id = "DM303"
    severity = Severity.HINT

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        if ctx.root.get("rngSeed") is None:
            yield ctx.diag(
                type(self),
                ctx.root,
                "No <setup rngSeed>: every run produces different data by design "
                "(the privacy-maximized default).",
                'Add rngSeed="1" (any int) to <setup> when you need identical replay '
                "(tests, fixtures, reviews).",
            )


class SeedForcesSingleProcess(Rule):
    id = "DM304"
    severity = Severity.HINT

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        if ctx.root.get("rngSeed") is None:
            return
        for element in ctx.iter():
            num_process = element.get("numProcess")
            if (num_process is not None and num_process.isdigit() and int(num_process) > 1) or _is_true(
                element.get("multiprocessing")
            ):
                yield ctx.diag(
                    type(self),
                    element,
                    "rngSeed forces single-process execution in CE — numProcess/multiprocessing "
                    "is silently ignored (seeded runs are serialized for reproducibility).",
                    "Drop numProcess/multiprocessing, or drop rngSeed if parallel throughput matters "
                    "more than replay.",
                )


class SmallPageSize(Rule):
    id = "DM305"
    severity = Severity.HINT

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_GENERATES):
            page_size = element.get("pageSize")
            if page_size is not None and page_size.isdigit() and int(page_size) < 100:
                yield ctx.diag(
                    type(self),
                    element,
                    f"pageSize={page_size} (<100) causes per-page overhead on every exporter and source.",
                    "Use pageSize >= 100, or omit it to let the engine size pages automatically.",
                )


class UpsertCoercesZeroCount(Rule):
    id = "DM307"
    severity = Severity.HINT

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_GENERATES):
            target = element.get("target") or ""
            if element.get("count") == "0" and ".upsert" in target:
                yield ctx.diag(
                    type(self),
                    element,
                    "count=\"0\" with a mongodb .upsert target is coerced to 1 — the engine still "
                    "upserts one (empty) document when the query matches nothing.",
                    "Expect exactly one upsert for zero matches, or drop the upsert target.",
                )


class PreferNativeNumericRange(Rule):
    id = "DM310"
    severity = Severity.HINT

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(EL_KEY, EL_ID, EL_VARIABLE, EL_NESTED_KEY):
            generator = element.get("generator") or ""
            if generator.startswith("IntegerGenerator(") and ("min" in generator or "max" in generator):
                yield ctx.diag(
                    type(self),
                    element,
                    "IntegerGenerator(...) eval-string used for a plain numeric range.",
                    'Prefer the native form: type="int" min="..." max="..." (validated attributes '
                    "instead of an eval-string).",
                )


class PreferNativeStringLength(Rule):
    id = "DM311"
    severity = Severity.HINT

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(EL_KEY, EL_ID, EL_VARIABLE, EL_NESTED_KEY):
            generator = element.get("generator") or ""
            if generator.startswith("StringGenerator("):
                yield ctx.diag(
                    type(self),
                    element,
                    "StringGenerator(...) eval-string used for string length bounds.",
                    'Prefer the native form: type="string" minLength="..." maxLength="...".',
                )


class InterpolationInScript(Rule):
    id = "DM314"
    severity = Severity.ERROR  # a bare __name__ in a Python expression is a NameError at runtime

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter():
            for attr in _SCRIPT_ATTRS:
                value = element.get(attr)
                if value and _INTERP_TOKEN.search(value):
                    token = _INTERP_TOKEN.search(value).group()  # type: ignore[union-attr]
                    yield ctx.diag(
                        type(self),
                        element,
                        f"{attr}=\"...\" is a Python expression, but it contains {token} — that is the "
                        "string-interpolation syntax (for string=/pattern=), not variable access.",
                        f"In {attr}= use the bare variable name: "
                        f"{token.strip('_')}.field, not {token}.field.",
                    )


RULES: tuple[type[Rule], ...] = (
    DistributionDefaultsToRandom,
    NonOrderedLoadsWholeSource,
    UnseededRunNotReproducible,
    SeedForcesSingleProcess,
    SmallPageSize,
    UpsertCoercesZeroCount,
    PreferNativeNumericRange,
    PreferNativeStringLength,
    InterpolationInScript,
)
