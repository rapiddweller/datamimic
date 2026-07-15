# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DM2xx — semantic rules the engine would raise on (fail-fast, one at a time).
Linting aggregates them and adds fix hints.

Constraint-derived rules are GENERIC: they iterate the declared ``__constraints__``
facts of every registered model via the schema index (LintContext.schemas, built by
build_schema_index()). Adding a fact to any model's ``__constraints__`` produces lint
coverage here with zero changes to this file — there are NO imports of model-private
constants and NO hard-coded tag lists tied to declared facts. ``lint_only=True`` facts
are checked too: they are exactly the lint layer's job (the engine executor skips them).

Where possible each rule still CALLS the same ModelUtil check the engine runs (SPOT);
the engine parse remains phase-2 authority for anything not covered here."""

from collections.abc import Callable, Iterable, Iterator  # noqa: I001
from dataclasses import replace

from lxml import etree
from pydantic import TypeAdapter, ValidationError

from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rules.base import LintContext, Rule
from datamimic_ce.constants.attribute_constants import (
    ATTR_DISTRIBUTION,
    ATTR_SOURCE,
    ATTR_TYPE,
    ATTR_UNIQUE,
)
from datamimic_ce.constants.element_constants import (
    EL_DATABASE,
    EL_GENERATE,
    EL_ITERATE,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_VARIABLE,
)
from datamimic_ce.model.constraints import (
    COUNT_XOR_MAX,
    COUNT_XOR_MIN,
    EXIST_COUNT,
    WEIGHTS_REQUIRE_VALUES,
    AllOrNone,
    AllowedValuesWhen,
    Constraint,
    Forbids,
    ForbidsWhenValue,
    MutuallyExclusive,
    MutuallyExclusiveWhen,
    RequiredOneOf,
    Requires,
    RequiresWhenValue,
    ValidValues,
    resolved_allowed,
    resolved_values,
)
from datamimic_ce.model.model_util import ModelUtil
from datamimic_ce.authoring.rule_catalog import RuleSeverity, authoring_rule_definition

_GENERATES = (EL_GENERATE, EL_ITERATE)

# Mirror of model_util._attr_true (module-private there, so re-declared): XML attribute
# strings are parsed exactly like the pydantic bool fields parse them ("true"/"True"/"1"/
# "yes"/"on" -> True); absent attributes and unparseable values are not truthy. Using the
# same TypeAdapter(bool) parse guarantees a when_true-gated lint check can never disagree
# with the engine's own gate.
_BOOL_ADAPTER = TypeAdapter(bool)


def _attr_true(value: str | None) -> bool:
    if value is None:
        return False
    try:
        return bool(_BOOL_ADAPTER.validate_python(value))
    except ValidationError:
        return False


def _constrained(ctx: LintContext) -> Iterator[tuple[etree._Element, tuple[Constraint, ...]]]:
    """Every element whose registered model declares constraint facts — read from the
    schema index (the registered source of truth), never from per-tag wiring here."""
    for element in ctx.iter():
        schema = ctx.schemas.get(str(element.tag))
        if schema is not None and schema.constraints:
            yield element, schema.constraints


def _gate_open(element: etree._Element, fact: Requires | Forbids) -> bool:
    """Requires/Forbids applicability gate: presence-based, or truthiness when when_true."""
    value = element.get(fact.attr)
    if fact.when_true:
        return _attr_true(value)
    return value is not None


def _is_unique_constraint(fact: Constraint) -> bool:
    """Whether DM204 owns this model-declared unique rule.

    This is semantic classification, not identity matching against global facts:
    <key> and source-backed models intentionally declare different distribution
    rules while sharing the same DM204 diagnostic contract.
    """
    if isinstance(fact, Requires | Forbids):
        return fact.attr == ATTR_UNIQUE
    return isinstance(fact, AllowedValuesWhen) and fact.when_attr == ATTR_UNIQUE


def _model_util_diag(
    rule: type[Rule],
    ctx: LintContext,
    element: etree._Element,
    check: "Callable[[dict[str, str]], object]",
    fix_context: str | None = None,
    severity: RuleSeverity | None = None,
) -> Diagnostic | None:
    """Run one engine-side ModelUtil check against the element's attributes."""
    try:
        check(dict(element.attrib))
    except ValueError as err:
        return ctx.diag(
            rule,
            element,
            evidence=f"runtime model check returned: {err}",
            fix_context=fix_context,
            severity=severity,
        )
    return None


def _constraint_check(constraints: tuple[Constraint, ...]) -> Callable[[dict[str, str]], object]:
    """Bind a fact tuple into the one-argument check contract used by lint rules."""

    def check(values: dict[str, str]) -> object:
        lint_constraints = tuple(replace(fact, lint_only=False) if fact.lint_only else fact for fact in constraints)
        return ModelUtil.check_constraints(values, lint_constraints)

    return check


# Facts OWNED by a dedicated rule below, so the generic handlers skip them instead
# of double-reporting:
# - COUNT_XOR_MIN/COUNT_XOR_MAX -> DM201 (tag-parameterized message + min<=max ordering)
# - EXIST_COUNT                 -> DM202 (time-series window interplay)
# - every unique-gated fact      -> DM204
# - WEIGHTS_REQUIRE_VALUES      -> DM203 (engine-error severity, historical id)
# A NEW model that declares one of these shared constants still gets coverage with zero
# changes here, because the owning rules derive their applicable elements from the index too.
_COUNT_RANGE_FACTS = (COUNT_XOR_MIN, COUNT_XOR_MAX)
_REQUIRES_OWNED_ELSEWHERE = (WEIGHTS_REQUIRE_VALUES,)
_RequiresGroupKey = tuple[frozenset[str], bool, str | None]


def _generation_mode_diag(
    rule: type[Rule],
    ctx: LintContext,
    element: etree._Element,
    fact: Constraint,
) -> Diagnostic | None:
    tag = str(element.tag)
    if isinstance(fact, MutuallyExclusive):
        if fact in _COUNT_RANGE_FACTS:
            return None
        modes = sorted(attr for attr in fact.attrs if element.get(attr) is not None)
        if len(modes) > 1:
            return ctx.diag(
                rule,
                element,
                evidence=f"<{tag}> sets modes {', '.join(modes)}",
                severity=rule.definition.severity_for(advisory=fact.lint_only),
            )
    if (
        isinstance(fact, RequiredOneOf)
        and fact != EXIST_COUNT
        and all(element.get(attr) is None for attr in fact.attrs)
    ):
        options = ", ".join(f"{attr}=" for attr in sorted(fact.attrs))
        return ctx.diag(
            rule,
            element,
            evidence=f"<{tag}> has no value source",
            fix_context=f"Available modes: {options}.",
            severity=rule.definition.severity_for(advisory=fact.lint_only),
        )
    return None


def _weights_require_values_diag(
    rule: type[Rule],
    ctx: LintContext,
    element: etree._Element,
    constraints: tuple[Constraint, ...],
) -> Diagnostic | None:
    if WEIGHTS_REQUIRE_VALUES not in constraints:
        return None
    return _model_util_diag(
        rule,
        ctx,
        element,
        ModelUtil.check_weights_require_values,
        fix_context="For weighted literals, add values=.",
    )


def _requires_violation(element: etree._Element, fact: Constraint) -> Requires | None:
    if not isinstance(fact, Requires):
        return None
    if fact in _REQUIRES_OWNED_ELSEWHERE or _is_unique_constraint(fact):
        return None
    if not _gate_open(element, fact):
        return None
    if any(element.get(need) is not None for need in fact.needs):
        return None
    return fact


def _requires_violations(
    element: etree._Element,
    constraints: tuple[Constraint, ...],
) -> dict[_RequiresGroupKey, list[str]]:
    violated: dict[_RequiresGroupKey, list[str]] = {}
    for candidate in constraints:
        fact = _requires_violation(element, candidate)
        if fact is not None:
            violated.setdefault((fact.needs, fact.lint_only, fact.message), []).append(
                fact.attr
            )
    return violated


def _source_companion_diag(
    rule: type[Rule],
    ctx: LintContext,
    element: etree._Element,
    key: _RequiresGroupKey,
    attrs: list[str],
) -> Diagnostic:
    needs, lint_only, declared_message = key
    present = ", ".join(sorted(attrs))
    severity = rule.definition.severity_for(advisory=lint_only)
    if declared_message is not None:
        return ctx.diag(
            rule,
            element,
            evidence=f"{declared_message}; present: {present}",
            fix_context=f"Required: {' or '.join(f'{need}=' for need in sorted(needs))}.",
            severity=severity,
        )
    if needs == frozenset((ATTR_SOURCE,)):
        return ctx.diag(
            rule,
            element,
            evidence=f"{present} is present without source=",
            severity=severity,
        )
    needed = " or ".join(f"{need}=" for need in sorted(needs))
    return ctx.diag(
        rule,
        element,
        evidence=f"{present} is present without {needed}",
        fix_context=f"Required: {needed}.",
        severity=severity,
    )


def _forbidden_companion_diag(
    rule: type[Rule],
    ctx: LintContext,
    element: etree._Element,
    fact: Constraint,
) -> Diagnostic | None:
    if not isinstance(fact, Forbids) or _is_unique_constraint(fact):
        return None
    if not _gate_open(element, fact):
        return None
    if fact.excludes_when_true:
        present = sorted(attr for attr in fact.excludes if _attr_true(element.get(attr)))
    else:
        present = sorted(attr for attr in fact.excludes if element.get(attr) is not None)
    if not present:
        return None
    tag = str(element.tag)
    message = fact.message or (
        f"<{tag}> {fact.attr}= cannot be combined with: {', '.join(present)}."
    )
    return ctx.diag(
        rule,
        element,
        evidence=f"{message} Present forbidden attributes: {', '.join(present)}",
        fix_context=f"Remove {', '.join(f'{attr}=' for attr in present)} or {fact.attr}=.",
        severity=rule.definition.severity_for(advisory=fact.lint_only),
    )


def _allowed_values_diag(
    rule: type[Rule],
    ctx: LintContext,
    element: etree._Element,
    fact: Constraint,
) -> Diagnostic | None:
    if not isinstance(fact, AllowedValuesWhen) or _is_unique_constraint(fact):
        return None
    gate_value = element.get(fact.when_attr)
    should_check = (not fact.when_true and fact.when_attr in element.attrib) or (
        fact.when_true and _attr_true(gate_value)
    )
    value = element.get(fact.attr)
    if not should_check or value is None:
        return None
    allowed = resolved_allowed(fact)
    if value in allowed:
        return None
    options = ", ".join(sorted(allowed))
    message = (
        fact.message.replace("{actual_value}", value)
        if fact.message is not None
        else f"when '{fact.when_attr}' is set, '{fact.attr}' value must be one of "
        f"[{options}], but got: '{value}'"
    )
    return ctx.diag(
        rule,
        element,
        evidence=f"{message} Actual {fact.attr}='{value}'",
        fix_context=f"Allowed values: {options}.",
        severity=rule.definition.severity_for(advisory=fact.lint_only),
    )


class CountBoundsConflict(Rule):
    definition = authoring_rule_definition("DM201")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            if COUNT_XOR_MIN not in constraints and COUNT_XOR_MAX not in constraints:
                continue
            tag = str(element.tag)

            def check_bounds(values: dict[str, str], _tag: str = tag) -> object:
                return ModelUtil.check_min_max_count(values, _tag)

            diag = _model_util_diag(
                type(self),
                ctx,
                element,
                check_bounds,
            )
            if diag:
                yield diag


class CountRequired(Rule):
    definition = authoring_rule_definition("DM202")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            if EXIST_COUNT not in constraints:
                continue
            # A fully-satisfied AllOrNone group (the <generate> time-series window
            # start/end/interval) switches the element into a mode where count is
            # optional (defaults to 1 series) — derived from the declared facts.
            if any(
                isinstance(fact, AllOrNone) and all(element.get(attr) is not None for attr in fact.attrs)
                for fact in constraints
            ):
                continue
            diag = _model_util_diag(
                type(self),
                ctx,
                element,
                ModelUtil.check_exist_count,
            )
            if diag:
                yield diag


class GenerationModeConflict(Rule):
    """Declared RequiredOneOf ('define at least one value source') and MutuallyExclusive
    ('mix at most one generation mode') facts, plus the weights=>values engine check.
    Historically scoped to <key>/<id>/<variable>; now driven purely by each model's
    declared facts, so any model declaring them is covered."""

    definition = authoring_rule_definition("DM203")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            for fact in constraints:
                diag = _generation_mode_diag(type(self), ctx, element, fact)
                if diag:
                    yield diag
            weights_diag = _weights_require_values_diag(type(self), ctx, element, constraints)
            if weights_diag:
                yield weights_diag


class UniqueConstraints(Rule):
    definition = authoring_rule_definition("DM204")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            if element.get("unique") is None:
                continue
            declared = tuple(fact for fact in constraints if _is_unique_constraint(fact))
            if not declared:
                continue

            diag = _model_util_diag(
                type(self),
                ctx,
                element,
                _constraint_check(declared),
            )
            if diag:
                yield diag


class SourceModeConflict(Rule):
    definition = authoring_rule_definition("DM205")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            for fact in constraints:
                if not isinstance(fact, MutuallyExclusiveWhen):
                    continue
                diag = _model_util_diag(
                    type(self),
                    ctx,
                    element,
                    _constraint_check((fact,)),
                    severity=type(self).definition.severity_for(advisory=fact.lint_only),
                )
                if diag:
                    yield diag


class CountDigitsOrScript(Rule):
    definition = authoring_rule_definition("DM212")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_GENERATES, EL_NESTED_KEY):
            count = element.get("count")
            if count is None:
                continue
            try:
                ModelUtil.check_is_digit_or_script(count)
            except ValueError as err:
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f"count='{count}', runtime parser returned: {err}",
                    fix_context='Examples: count="100" or count="{customers * 3}".',
                )


class NestedKeyCyclicNeedsCount(Rule):
    definition = authoring_rule_definition("DM213")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(EL_NESTED_KEY):
            cyclic = element.get("cyclic")
            has_count = any(element.get(a) is not None for a in ("count", "minCount", "maxCount"))
            if cyclic is not None and cyclic.lower() in ("true", "1") and not has_count:
                yield ctx.diag(
                    type(self),
                    element,
                    evidence='cyclic="True" without count/minCount/maxCount',
                    fix_context="A cyclic generate is different: it can fall back to source length.",
                )


class SourceCompanionsWithoutSource(Rule):
    """Declared Requires facts, checked generically. Facts needing source= are grouped
    into one diagnostic per severity and element (the historical DM214 shape: cyclic/selector/separator/
    sourceScripted/weightColumn, plus the lint_only iterationSelector fact); facts with
    other needs-sets (e.g. dataset=>generator|entity, defaultValue=>script) report per
    needs-group. Engine-enforced facts are errors; lint-only guidance remains a warning."""

    definition = authoring_rule_definition("DM214")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            violations = _requires_violations(element, constraints)
            ordered = sorted(
                violations.items(),
                key=lambda item: (sorted(item[0][0]), item[0][1], item[0][2] or ""),
            )
            for key, attrs in ordered:
                yield _source_companion_diag(type(self), ctx, element, key, attrs)


class NestedKeyNeedsType(Rule):
    definition = authoring_rule_definition("DM216")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(EL_NESTED_KEY):
            has_children = any(isinstance(child.tag, str) and child.tag != "comment" for child in element)
            drives_data = any(element.get(a) is not None for a in ("type", "source", "script"))
            if has_children and not drives_data:
                # Engine falls into template-enrichment mode -> KeyError unless the record
                # already carries a field of this name (rare, from a scripted source template).
                yield ctx.diag(
                    type(self),
                    element,
                    evidence="nestedKey has children but no type/source/script",
                )


class SelectorWithoutCountNeedsDbSource(Rule):
    """selector= without count=/minCount=/maxCount= only resolves against a DatabaseClient
    (MongoDB, relational DB) — mirrors generate_task.py:87-90, variable_task.py:105.
    Deliberately excludes <nestedKey>: it resolves its length from count/minCount/maxCount and
    falls back to the loaded value's length otherwise (nested_key_task.py:
    _determine_nestedkey_length), never routing through the DatabaseClient-only check."""

    definition = authoring_rule_definition("DM211")

    _DB_CLIENT_TAGS = (EL_DATABASE, EL_MONGODB)

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        db_ids = {el.get("id") for el in ctx.iter(*self._DB_CLIENT_TAGS) if el.get("id")}
        for element in ctx.iter(*_GENERATES, EL_VARIABLE):
            if element.get("selector") is None:
                continue
            if any(element.get(a) is not None for a in ("count", "minCount", "maxCount")):
                continue
            source = element.get("source")
            if source is not None and source in db_ids:
                continue  # resolves to a declared <database>/<mongodb> client — valid
            yield ctx.diag(
                type(self),
                element,
                evidence=f"selector is unbounded and source='{source}' is not a declared DB client",
            )


class AllOrNoneGroup(Rule):
    """Declared AllOrNone facts (e.g. the <generate> time-series window start/end/interval):
    setting only part of the group is an engine error — report every missing attr at once."""

    definition = authoring_rule_definition("DM217")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            tag = str(element.tag)
            for fact in constraints:
                if not isinstance(fact, AllOrNone):
                    continue
                present = sorted(attr for attr in fact.attrs if element.get(attr) is not None)
                if not present or len(present) == len(fact.attrs):
                    continue
                missing = sorted(attr for attr in fact.attrs if element.get(attr) is None)
                message = fact.message or (
                    f"<{tag}> sets {', '.join(present)} but not {', '.join(missing)} — "
                    "these attributes only work as a complete group."
                )
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f"{message} Present={present}; missing={missing}",
                    fix_context=f"Missing: {', '.join(f'{attr}=' for attr in missing)}.",
                    severity=type(self).definition.severity_for(advisory=fact.lint_only),
                )


class ForbiddenCompanions(Rule):
    """Declared Forbids facts (e.g. <nestedKey script=> forbids type/source/sourceScripted/
    separator). unique=>no-weights/cyclic is owned by DM204."""

    definition = authoring_rule_definition("DM218")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            for fact in constraints:
                diag = _forbidden_companion_diag(type(self), ctx, element, fact)
                if diag:
                    yield diag


class DeclaredValidValues(Rule):
    """Declared ValidValues facts for NON-type attributes (e.g. <variable storage=>).

    type= is deliberately excluded here: DM105 (schema_rules) owns type= with tag-specific
    extensions the raw facts don't know about — the source-read exemption on <variable>/
    <nestedKey> (type= names a producer, not a scalar cast), the list/dict structural
    markers, and the date-type fix hints. Checking type facts here would double-report
    every DM105 finding on <key>/<id>. ValidValues-on-type facts of models DM105 does not
    type-check (<array>, <execute>) stay enforced by their field validators, surfaced via
    the phase-2 engine parse."""

    definition = authoring_rule_definition("DM219")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            for fact in constraints:
                if not isinstance(fact, ValidValues) or fact.attr in (ATTR_TYPE, ATTR_DISTRIBUTION):
                    continue
                value = element.get(fact.attr)
                if value is None:
                    continue
                valid = resolved_values(fact)
                if value in valid:
                    continue
                options = ", ".join(sorted(valid))
                message = fact.message or f"'{fact.attr}' value must be one of [{options}], but got: '{value}'"
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f"{message} Actual {fact.attr}='{value}'",
                    fix_context=f"Allowed values: {options}.",
                    severity=type(self).definition.severity_for(advisory=fact.lint_only),
                )


class AllowedValuesWhenConstraint(Rule):
    """Declared AllowedValuesWhen facts: when a gate attr is present/truthy, another attr
    if PRESENT must be in the set of allowed values. Unique-gated facts are owned by
    DM204; all other declarations are handled here without model-specific wiring."""

    definition = authoring_rule_definition("DM220")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            for fact in constraints:
                diag = _allowed_values_diag(type(self), ctx, element, fact)
                if diag:
                    yield diag


class ConditionalDeclaredConstraints(Rule):
    """Value-gated and mode-gated central facts not owned by a legacy DM rule."""

    definition = authoring_rule_definition("DM221")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element, constraints in _constrained(ctx):
            for fact in constraints:
                if isinstance(fact, MutuallyExclusiveWhen):
                    continue  # DM205 owns mode-gated mutual exclusion
                if not isinstance(fact, RequiresWhenValue | ForbidsWhenValue):
                    continue
                diag = _model_util_diag(
                    type(self),
                    ctx,
                    element,
                    _constraint_check((fact,)),
                    severity=type(self).definition.severity_for(advisory=fact.lint_only),
                )
                if diag:
                    yield diag


RULES: tuple[type[Rule], ...] = (
    CountBoundsConflict,
    CountRequired,
    GenerationModeConflict,
    UniqueConstraints,
    SourceModeConflict,
    CountDigitsOrScript,
    NestedKeyCyclicNeedsCount,
    SourceCompanionsWithoutSource,
    NestedKeyNeedsType,
    SelectorWithoutCountNeedsDbSource,
    AllOrNoneGroup,
    ForbiddenCompanions,
    DeclaredValidValues,
    AllowedValuesWhenConstraint,
    ConditionalDeclaredConstraints,
)
