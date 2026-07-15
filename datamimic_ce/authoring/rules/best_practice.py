# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DM3xx — best-practice rules where the ENGINE STAYS SILENT and does something
surprising. These are the linter's flagship rules: nothing else catches them."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from math import isfinite

from lxml import etree

from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rule_catalog import authoring_rule_definition
from datamimic_ce.authoring.rules.base import LintContext, Rule
from datamimic_ce.constants.data_type_constants import DATA_TYPE_DECIMAL, DATA_TYPE_FLOAT, DATA_TYPE_INT
from datamimic_ce.constants.element_constants import (
    EL_CONDITION,
    EL_ELSE,
    EL_ELSE_IF,
    EL_GENERATE,
    EL_ID,
    EL_IF,
    EL_ITERATE,
    EL_KEY,
    EL_NESTED_KEY,
    EL_REFERENCE,
    EL_VARIABLE,
)
from datamimic_ce.enums.distribution_enums import POSITIONAL_NUMBER_SEQUENCES, NumberDistribution
from datamimic_ce.utils.number_sequences import finite_number_sequence_capacity

_GENERATES = (EL_GENERATE, EL_ITERATE)
_SOURCE_READERS = (*_GENERATES, EL_VARIABLE, EL_NESTED_KEY, EL_REFERENCE)

# A bare __name__ token (the string-interpolation syntax) used as an identifier —
# not `.__dunder__` attribute access, which is legitimate Python.
_INTERP_TOKEN = re.compile(r"(?<![\w.])__[A-Za-z]\w*__")
# Attributes evaluated as Python expressions, where __var__ interpolation does NOT apply.
_SCRIPT_ATTRS = ("script", "condition")
_CONDITIONAL_TAGS = (EL_CONDITION, EL_IF, EL_ELSE_IF, EL_ELSE)


def _is_true(value: str | None) -> bool:
    return value is not None and value.lower() in ("true", "1")


@dataclass(frozen=True)
class _NestedSequenceAnalysis:
    element: etree._Element
    distribution: NumberDistribution
    capacity: int
    demand: int | None
    unknown_reason: str | None


def _sequence_capacity(element: etree._Element) -> tuple[NumberDistribution, int] | None:
    """Resolve capacity from the same enum and iterator helper as runtime generation."""
    raw_distribution = element.get("distribution")
    if raw_distribution is None:
        return None
    try:
        distribution = NumberDistribution(raw_distribution)
    except ValueError:
        return None  # DM105 owns unknown distribution values
    if distribution not in POSITIONAL_NUMBER_SEQUENCES:
        return None

    data_type = element.get("type")
    if data_type == DATA_TYPE_INT:
        defaults = (Decimal(0), Decimal(1_000_000), Decimal(1))
    elif data_type in (DATA_TYPE_FLOAT, DATA_TYPE_DECIMAL):
        defaults = (Decimal(0), Decimal(10), Decimal("0.1"))
    else:
        return None  # central type/range constraints own invalid shapes
    min_raw = element.get("min")
    max_raw = element.get("max")
    granularity_raw = element.get("granularity")
    try:
        min_v = Decimal(min_raw) if min_raw is not None else defaults[0]
        max_v = Decimal(max_raw) if max_raw is not None else defaults[1]
        granularity = (
            Decimal(granularity_raw)
            if data_type in (DATA_TYPE_FLOAT, DATA_TYPE_DECIMAL) and granularity_raw is not None
            else defaults[2]
        )
    except InvalidOperation:
        return None
    if not all(value.is_finite() for value in (min_v, max_v, granularity)):
        return None
    numeric_bounds = (float(min_v), float(max_v), float(granularity))
    if not all(isfinite(value) for value in numeric_bounds):
        return None
    capacity = finite_number_sequence_capacity(
        distribution,
        *numeric_bounds,
    )
    return (distribution, capacity) if capacity is not None else None


def _literal_nested_demand(
    element: etree._Element,
    cardinality_scopes: list[etree._Element],
) -> tuple[int | None, str | None]:
    """Prove total uses of one root-cached sequence, or explain why it is dynamic."""
    conditional_reason = _conditional_demand_reason(element)
    if conditional_reason is not None:
        return None, conditional_reason

    demand = 1
    for scope in cardinality_scopes:
        factor, unknown_reason = _literal_scope_factor(scope)
        if unknown_reason is not None:
            return None, unknown_reason
        demand *= factor
    return demand, None


def _conditional_demand_reason(element: etree._Element) -> str | None:
    if element.get("condition") is not None:
        return "a condition can change how many rows evaluate the field"
    if any(isinstance(ancestor.tag, str) and ancestor.tag in _CONDITIONAL_TAGS for ancestor in element.iterancestors()):
        return "a condition can change how many rows evaluate the field"
    return None


def _literal_scope_factor(scope: etree._Element) -> tuple[int, str | None]:
    scope_tag = scope.tag.decode() if isinstance(scope.tag, bytes) else str(scope.tag)
    scope_name = scope.get("name") or ""
    if scope.get("condition") is not None:
        return 1, f"<{scope_tag}> '{scope_name}' has condition= and may be skipped"
    if scope.get("source") is not None or scope.get("script") is not None:
        return 1, f"<{scope_tag}> '{scope_name}' derives cardinality from source/script"
    dynamic_attrs = ("start", "end", "interval", "minCount", "maxCount")
    if any(scope.get(attr) is not None for attr in dynamic_attrs):
        return 1, f"<{scope_tag}> '{scope_name}' has non-literal cardinality semantics"
    count = scope.get("count")
    if scope_tag == EL_NESTED_KEY and count is None and scope.get("type") == "dict":
        return 1, None
    if count is None or not count.isdigit():
        return 1, f"<{scope_tag}> '{scope_name}' does not have a literal count"
    return int(count), None


def _nested_sequence_analyses(ctx: LintContext) -> Iterable[_NestedSequenceAnalysis]:
    for element in ctx.iter(EL_KEY, EL_ID):
        resolved = _sequence_capacity(element)
        if resolved is None:
            continue
        cardinality_scopes = [
            ancestor
            for ancestor in element.iterancestors()
            if isinstance(ancestor.tag, str) and ancestor.tag in (*_GENERATES, EL_NESTED_KEY)
        ]
        generate_scope_count = sum(scope.tag in _GENERATES for scope in cardinality_scopes)
        has_nested_key_scope = any(scope.tag == EL_NESTED_KEY for scope in cardinality_scopes)
        if generate_scope_count < 2 and not has_nested_key_scope:
            continue  # a field directly in one top-level generate is intentionally out of scope
        distribution, capacity = resolved
        demand, unknown_reason = _literal_nested_demand(element, cardinality_scopes)
        yield _NestedSequenceAnalysis(element, distribution, capacity, demand, unknown_reason)


class DistributionDefaultsToRandom(Rule):
    definition = authoring_rule_definition("DM301")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_SOURCE_READERS):
            if element.get("source") is not None and element.get("distribution") is None:
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f'source="{element.get("source")}" has no distribution',
                )


class NonOrderedLoadsWholeSource(Rule):
    definition = authoring_rule_definition("DM302")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_SOURCE_READERS):
            if element.get("source") is None:
                continue
            distribution = element.get("distribution")
            if distribution in ("random", "cumulated") or _is_true(element.get("unique")):
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f"distribution='{distribution or 'random'}', unique={_is_true(element.get('unique'))}",
                )


class UnseededRunNotReproducible(Rule):
    definition = authoring_rule_definition("DM303")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        if ctx.root.get("rngSeed") is None:
            yield ctx.diag(type(self), ctx.root)


class SeedForcesSingleProcess(Rule):
    definition = authoring_rule_definition("DM304")

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
                    evidence=f"numProcess={num_process}, multiprocessing={element.get('multiprocessing')}",
                )


class SmallPageSize(Rule):
    definition = authoring_rule_definition("DM305")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_GENERATES):
            page_size = element.get("pageSize")
            if page_size is not None and page_size.isdigit() and int(page_size) < 100:
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f"pageSize={page_size}",
                )


class UpsertCoercesZeroCount(Rule):
    definition = authoring_rule_definition("DM307")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_GENERATES):
            target = element.get("target") or ""
            if element.get("count") == "0" and ".upsert" in target:
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f'count="0", target="{target}"',
                )


class PreferNativeNumericRange(Rule):
    definition = authoring_rule_definition("DM310")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(EL_KEY, EL_ID, EL_VARIABLE, EL_NESTED_KEY):
            generator = element.get("generator") or ""
            if generator.startswith("IntegerGenerator(") and ("min" in generator or "max" in generator):
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f'generator="{generator}"',
                )


class PreferNativeStringLength(Rule):
    definition = authoring_rule_definition("DM311")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(EL_KEY, EL_ID, EL_VARIABLE, EL_NESTED_KEY):
            generator = element.get("generator") or ""
            if generator.startswith("StringGenerator("):
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f'generator="{generator}"',
                )


class InterpolationInScript(Rule):
    definition = authoring_rule_definition("DM314")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter():
            for attr in _SCRIPT_ATTRS:
                value = element.get(attr)
                if value and _INTERP_TOKEN.search(value):
                    token = _INTERP_TOKEN.search(value).group()  # type: ignore[union-attr]
                    yield ctx.diag(
                        type(self),
                        element,
                        evidence=f"{attr} contains interpolation token {token}",
                        fix_context=f"Use {token.strip('_')}.field in {attr}=.",
                    )


class IncrementCountsPerParentInNestedGenerate(Rule):
    definition = authoring_rule_definition("DM315")

    # bare literal forms only — IncrementGenerator(start=...) etc. is a deliberate choice
    _INCREMENT_FORMS = ("IncrementGenerator", "IncrementGenerator()")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(EL_KEY, EL_ID):
            generator = (element.get("generator") or "").strip()
            if generator not in self._INCREMENT_FORMS:
                continue
            # Structural fact: the key's nearest enclosing scope is a generate/iterate
            # (keys inside <nestedKey> are per-record lists, not per-parent id sequences)
            # that itself sits inside another generate/iterate. <condition>/<if> wrappers
            # are not scopes and pass through.
            scopes = [
                anc
                for anc in element.iterancestors()
                if isinstance(anc.tag, str) and anc.tag in (*_GENERATES, EL_NESTED_KEY)
            ]
            if scopes and scopes[0].tag in _GENERATES and any(anc.tag in _GENERATES for anc in scopes[1:]):
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f"field '{element.get('name')}' is inside nested <generate>",
                    fix_context='Example: script="parent.customer_id * 100 + this.line_no".',
                )


class NestedFiniteSequenceExhaustion(Rule):
    definition = authoring_rule_definition("DM317")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for analysis in _nested_sequence_analyses(ctx):
            if analysis.demand is None or analysis.capacity >= analysis.demand:
                continue
            yield ctx.diag(
                type(self),
                analysis.element,
                evidence=f"distribution='{analysis.distribution.value}', capacity={analysis.capacity}, "
                f"demand={analysis.demand}",
            )


class NestedFiniteSequenceCardinalityUnknown(Rule):
    definition = authoring_rule_definition("DM318")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for analysis in _nested_sequence_analyses(ctx):
            if analysis.demand is not None:
                continue
            yield ctx.diag(
                type(self),
                analysis.element,
                evidence=f"distribution='{analysis.distribution.value}', capacity={analysis.capacity}; "
                f"unknown because {analysis.unknown_reason}",
            )


class CountWithSourceCapsSilently(Rule):
    definition = authoring_rule_definition("DM316")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        from datamimic_ce.enums.distribution_enums import SourceDistribution

        for element in ctx.iter(*_GENERATES):
            count = element.get("count")
            if (
                element.get("source") is not None
                and count is not None
                and count.isdigit()  # {script} counts are unknowable here
                and not _is_true(element.get("cyclic"))
                # cumulated samples WITH replacement — it never runs out, so no cap
                and element.get("distribution") != SourceDistribution.CUMULATED.value
            ):
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f'count="{count}", source="{element.get("source")}"',
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
    IncrementCountsPerParentInNestedGenerate,
    NestedFiniteSequenceExhaustion,
    NestedFiniteSequenceCardinalityUnknown,
    CountWithSourceCapsSilently,
)
