# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DM2xx — semantic rules the engine would raise on (fail-fast, one at a time).
Linting aggregates them and adds fix hints. Where possible each rule CALLS the
same ModelUtil check the engine runs (SPOT); the engine parse remains phase-2
authority for anything not covered here."""

from collections.abc import Callable, Iterable

from lxml import etree

from datamimic_ce.authoring.diagnostics import Diagnostic, Severity
from datamimic_ce.authoring.rules.base import LintContext, Rule
from datamimic_ce.constants.element_constants import (
    EL_DATABASE,
    EL_GENERATE,
    EL_ID,
    EL_ITERATE,
    EL_KEY,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_VARIABLE,
)
from datamimic_ce.model.model_util import ModelUtil

_GENERATES = (EL_GENERATE, EL_ITERATE)
_TIMESERIES = ("start", "end", "interval")
_KEY_MODES = ("source", "values", "script", "generator", "constant", "pattern")


def _model_util_diag(
    rule: type[Rule],
    ctx: LintContext,
    element: etree._Element,
    check: "Callable[[dict[str, str]], object]",
    fix_hint: str,
) -> Diagnostic | None:
    """Run one engine-side ModelUtil check against the element's attributes."""
    try:
        check(dict(element.attrib))
    except ValueError as err:
        return ctx.diag(rule, element, str(err), fix_hint)
    return None


class CountBoundsConflict(Rule):
    id = "DM201"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_GENERATES, EL_NESTED_KEY):
            tag = str(element.tag)

            def check_bounds(values: dict[str, str], _tag: str = tag) -> object:
                return ModelUtil.check_min_max_count(values, _tag)

            diag = _model_util_diag(
                type(self),
                ctx,
                element,
                check_bounds,
                "Use either count, or a minCount/maxCount range (with minCount <= maxCount) — never both.",
            )
            if diag:
                yield diag


class CountRequired(Rule):
    id = "DM202"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_GENERATES):
            if all(element.get(attr) is not None for attr in _TIMESERIES):
                continue  # time-series mode: count optional (defaults to 1 series)
            diag = _model_util_diag(
                type(self),
                ctx,
                element,
                ModelUtil.check_exist_count,
                "Add count=\"N\" (or minCount/maxCount), or provide a source/script that supplies the rows.",
            )
            if diag:
                yield diag


class KeyGenerationMode(Rule):
    id = "DM203"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(EL_KEY, EL_ID):
            tag = str(element.tag)
            modes = [mode for mode in _KEY_MODES if element.get(mode) is not None]
            if len(modes) > 1:
                yield ctx.diag(
                    type(self),
                    element,
                    f"<{tag}> mixes generation modes: {', '.join(modes)}.",
                    "Keep exactly one value source per key (e.g. only generator=, or only values=).",
                )
            elif not modes and not any(element.get(a) is not None for a in ("type", "string")):
                yield ctx.diag(
                    type(self),
                    element,
                    f"<{tag}> defines no value source.",
                    "Add one of: type= (with min/max), generator=, values=, constant=, script=, pattern=, "
                    "source=, or string=.",
                )
            diag = _model_util_diag(
                type(self),
                ctx,
                element,
                ModelUtil.check_weights_require_values,
                "weights= is only allowed together with values=.",
            )
            if diag:
                yield diag


class UniqueConstraints(Rule):
    id = "DM204"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter():
            if element.get("unique") is None:
                continue
            diag = _model_util_diag(
                type(self),
                ctx,
                element,
                ModelUtil.check_unique_constraints,
                "unique needs a finite pool (values= or source=) and only combines with "
                "distribution=\"random\" (the default) — drop weights/cyclic/ordered/cumulated.",
            )
            if diag:
                yield diag


class SourceModeConflict(Rule):
    id = "DM205"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_GENERATES, EL_VARIABLE):
            if element.get("source") is None:
                continue
            diag = _model_util_diag(
                type(self),
                ctx,
                element,
                ModelUtil.check_generation_mode_of_source,
                "When reading from source=, pick ONE of type= (or sourceEntity=) OR selector= — not both.",
            )
            if diag:
                yield diag


class CountDigitsOrScript(Rule):
    id = "DM212"
    severity = Severity.ERROR

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
                    str(err),
                    'count is digits ("100") or a {script} expression (count="{customers * 3}").',
                )


class NestedKeyCyclicNeedsCount(Rule):
    id = "DM213"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(EL_NESTED_KEY):
            cyclic = element.get("cyclic")
            has_count = any(element.get(a) is not None for a in ("count", "minCount", "maxCount"))
            if cyclic is not None and cyclic.lower() in ("true", "1") and not has_count:
                yield ctx.diag(
                    type(self),
                    element,
                    "<nestedKey cyclic=\"True\"> without a count would loop forever.",
                    "Add count= (or minCount/maxCount) to the <nestedKey>. "
                    "(<generate cyclic> is fine without count — it falls back to the source length.)",
                )


class SourceCompanionsWithoutSource(Rule):
    id = "DM214"
    severity = Severity.WARNING

    _COMPANIONS = ("cyclic", "selector", "separator", "sourceScripted", "iterationSelector", "weightColumn")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter(*_GENERATES, EL_VARIABLE, EL_NESTED_KEY):
            if element.get("source") is not None:
                continue
            present = [attr for attr in self._COMPANIONS if element.get(attr) is not None]
            if present:
                yield ctx.diag(
                    type(self),
                    element,
                    f"{', '.join(present)} only take effect together with source= (none is set).",
                    "Add source=..., or remove the attribute(s).",
                )


class NestedKeyNeedsType(Rule):
    id = "DM216"
    severity = Severity.WARNING  # no-type is valid template-enrichment, but only if the field pre-exists

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
                    "<nestedKey> with child fields but no type/source/script builds nothing — the "
                    "engine expects the field to already exist and raises KeyError otherwise.",
                    'Add type="list" (with count/minCount/maxCount) for a list of records, or '
                    'type="dict" for one nested object.',
                )


class SelectorWithoutCountNeedsDbSource(Rule):
    """selector= without count=/minCount=/maxCount= only resolves against a DatabaseClient
    (MongoDB, relational DB) — mirrors generate_task.py:87-90, variable_task.py:105.
    Deliberately excludes <nestedKey>: it resolves its length from count/minCount/maxCount and
    falls back to the loaded value's length otherwise (nested_key_task.py:
    _determine_nestedkey_length), never routing through the DatabaseClient-only check."""

    id = "DM211"
    severity = Severity.ERROR

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
                "selector= without count=/minCount=/maxCount= only works when source= "
                "resolves to a <database> or <mongodb> client.",
                'Add count= (or minCount/maxCount), or point source= at a declared '
                '<database id="..."> / <mongodb id="...">.',
            )


RULES: tuple[type[Rule], ...] = (
    CountBoundsConflict,
    CountRequired,
    KeyGenerationMode,
    UniqueConstraints,
    SourceModeConflict,
    CountDigitsOrScript,
    NestedKeyCyclicNeedsCount,
    SourceCompanionsWithoutSource,
    NestedKeyNeedsType,
    SelectorWithoutCountNeedsDbSource,
)
