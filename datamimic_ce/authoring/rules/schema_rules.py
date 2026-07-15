# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DM1xx — syntax/schema rules, driven entirely by the derived SchemaIndex
(model_fields + nesting table): unknown elements/attributes, nesting, required
attributes, enum values. No hand-copied schema knowledge."""

import difflib
from collections.abc import Iterable

from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rules.base import LintContext, Rule
from datamimic_ce.constants.data_type_constants import (
    DATA_TYPE_DICT,
    DATA_TYPE_LIST,
)
from datamimic_ce.constants.element_constants import (
    EL_COMMENT,
    EL_ID,
    EL_KEY,
    EL_NESTED_KEY,
    EL_SETUP,
    EL_VARIABLE,
)
from datamimic_ce.model.constraints import (
    KEY_DISTRIBUTION_VALUES,
    ValidValues,
    resolved_values,
)
from datamimic_ce.authoring.rule_catalog import authoring_rule_definition

_DATE_TYPE_GUESSES = {"datetime", "date", "timestamp", "time"}


def _key_id_data_types(ctx: LintContext) -> frozenset[str]:
    """<key>/<id> valid scalar types, read from KeyModel's declared ValidValues(type=) fact
    via the schema index (the registered source — no private model-constant import)."""
    schema = ctx.schemas.get(EL_KEY)
    if schema is not None:
        for fact in schema.constraints:
            if isinstance(fact, ValidValues) and fact.attr == "type":
                return resolved_values(fact)
    return frozenset()


def _distribution_fact(ctx: LintContext, tag: str) -> ValidValues | None:
    """Read a tag's distribution vocabulary from its central model contract."""
    schema = ctx.schemas.get(tag)
    if schema is None:
        return None
    return next(
        (fact for fact in schema.constraints if isinstance(fact, ValidValues) and fact.attr == "distribution"),
        None,
    )


class RootIsSetup(Rule):
    definition = authoring_rule_definition("DM106")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        root_tag = str(ctx.root.tag)
        if root_tag != EL_SETUP:
            yield ctx.diag(
                type(self),
                ctx.root,
                evidence=f"root is <{root_tag}>",
            )


class UnknownElement(Rule):
    definition = authoring_rule_definition("DM101")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        known = ctx.schemas.tags
        for element in ctx.iter():
            tag = str(element.tag)
            if tag not in known:
                suggestion = difflib.get_close_matches(tag, sorted(known), n=1)
                hint = (
                    f"Did you mean <{suggestion[0]}>?" if suggestion else f"Known elements: {', '.join(sorted(known))}."
                )
                yield ctx.diag(
                    type(self),
                    element,
                    evidence=f"element is <{tag}>",
                    fix_context=hint,
                )


class InvalidChild(Rule):
    definition = authoring_rule_definition("DM102")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter():
            tag = str(element.tag)
            schema = ctx.schemas.get(tag)
            if schema is None or schema.allowed_children is None or not schema.allowed_children:
                continue  # unknown (DM101), free nesting, or leaf (DM107)
            for child in element:
                if not isinstance(child.tag, str) or child.tag == EL_COMMENT:
                    continue
                if child.tag not in schema.allowed_children and child.tag in ctx.schemas.tags:
                    yield ctx.diag(
                        type(self),
                        child,
                        evidence=f"<{child.tag}> appears inside <{tag}>",
                        fix_context=f"<{tag}> accepts: {', '.join(sorted(schema.allowed_children))}.",
                    )


class LeafHasChildren(Rule):
    definition = authoring_rule_definition("DM107")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter():
            tag = str(element.tag)
            schema = ctx.schemas.get(tag)
            if schema is None or schema.allowed_children is None or schema.allowed_children:
                continue
            for child in element:
                if isinstance(child.tag, str) and child.tag != EL_COMMENT:
                    yield ctx.diag(
                        type(self),
                        child,
                        evidence=f"<{tag}> contains <{child.tag}>",
                        fix_context=f"Remove <{child.tag}> or move it to a container element.",
                    )


class UnknownAttribute(Rule):
    definition = authoring_rule_definition("DM103")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter():
            tag = str(element.tag)
            schema = ctx.schemas.get(tag)
            if schema is None or schema.model is None or schema.open_attrs:
                continue  # unknown element, no attribute schema, or credentials-style open model
            valid = set(schema.attributes)
            for attr in element.attrib:
                attr_name = str(attr)
                if attr_name not in valid:
                    suggestion = difflib.get_close_matches(attr_name, sorted(valid), n=1)
                    hint = (
                        f"Did you mean '{suggestion[0]}'?"
                        if suggestion
                        else f"Valid attributes: {', '.join(sorted(valid))}."
                    )
                    yield ctx.diag(
                        type(self),
                        element,
                        evidence=f"attribute '{attr_name}' appears on <{tag}>",
                        fix_context=hint,
                    )


class MissingRequiredAttribute(Rule):
    definition = authoring_rule_definition("DM104")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter():
            tag = str(element.tag)
            schema = ctx.schemas.get(tag)
            # open_attrs models (<database>/<mongodb>) get their required credentials
            # fulfilled from conf/{env}.env.properties — not from XML attributes
            if schema is None or schema.model is None or schema.open_attrs:
                continue
            for spec in schema.attributes.values():
                if spec.required and spec.name not in element.attrib:
                    yield ctx.diag(
                        type(self),
                        element,
                        evidence=f"<{tag}> is missing '{spec.name}'",
                        fix_context=f'Add {spec.name}="..." to <{tag}>.',
                    )


class InvalidAttributeValue(Rule):
    definition = authoring_rule_definition("DM105")

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        key_id_data_types = _key_id_data_types(ctx)
        # NestedKey/Variable: declare no type enforcement at parse today (per plan R5).
        # Extend lint set to include structural markers (list/dict) in addition to scalar
        # core. This is a lint-only extension; engine-side enforcement is out of scope.
        nestedkey_variable_data_types = key_id_data_types | {DATA_TYPE_LIST, DATA_TYPE_DICT}
        for element in ctx.iter():
            tag = str(element.tag)
            distribution = element.get("distribution")
            if distribution is not None:
                distribution_fact = _distribution_fact(ctx, tag)
                valid_distributions = (
                    resolved_values(distribution_fact) if distribution_fact is not None else frozenset()
                )
                if distribution_fact is not None and distribution not in valid_distributions:
                    if distribution_fact is KEY_DISTRIBUTION_VALUES:
                        hint = (
                            f"<{tag}>'s distribution shapes a numeric range (needs "
                            f'type="int"/"float"/"decimal" with min=/max=). Use one of: '
                            f"{', '.join(sorted(valid_distributions))}."
                        )
                    else:
                        hint = f"Use one of: {', '.join(sorted(valid_distributions))}."
                    yield ctx.diag(
                        type(self),
                        element,
                        evidence=f"distribution='{distribution}' on <{tag}>",
                        fix_context=hint,
                    )
            # On <variable>/<nestedKey> WITH a source=, type= is not a scalar cast — it's the
            # sourceEntity->type->name physical-entity fallback (StatementUtil.resolve_source_entity,
            # e.g. selecting which producer's rows to read back from a <memstore>) and can be any
            # string. <key>/<id> never read a source (key_task.py ignores KeyModel.source), so their
            # type= is always the scalar cast and always checked.
            reads_source = tag in (EL_VARIABLE, EL_NESTED_KEY) and element.get("source")
            if tag in (EL_KEY, EL_ID, EL_NESTED_KEY, EL_VARIABLE) and not reads_source:
                # Use the appropriate type set per tag (C-2 fix: key/id accept only 6 scalar types)
                valid_types = key_id_data_types if tag in (EL_KEY, EL_ID) else nestedkey_variable_data_types
                type_value = element.get("type")
                if type_value is not None and type_value not in valid_types:
                    if type_value.lower() in _DATE_TYPE_GUESSES:
                        hint = (
                            "DATAMIMIC has no scalar date/time type. For a timestamp field use "
                            'generator="DateTimeGenerator" (or, inside a time-series <generate '
                            'start= end= interval=>, script="ts.now").'
                        )
                    else:
                        hint = f"Use one of: {', '.join(sorted(valid_types))}."
                    yield ctx.diag(
                        type(self),
                        element,
                        evidence=f"type='{type_value}' on <{tag}>",
                        fix_context=hint,
                    )
            schema = ctx.schemas.get(tag)
            if schema is None:
                continue
            for attr, value in element.attrib.items():
                spec = schema.attributes.get(str(attr))
                value_str = str(value)
                if spec is not None and "int" in spec.annotation and not value_str.lstrip("-").isdigit():
                    yield ctx.diag(
                        type(self),
                        element,
                        evidence=f"attribute '{attr!s}' has non-integer value '{value_str}'",
                        fix_context=f"Set {attr!s} to a whole number.",
                    )


RULES: tuple[type[Rule], ...] = (
    RootIsSetup,
    UnknownElement,
    InvalidChild,
    LeafHasChildren,
    UnknownAttribute,
    MissingRequiredAttribute,
    InvalidAttributeValue,
)
