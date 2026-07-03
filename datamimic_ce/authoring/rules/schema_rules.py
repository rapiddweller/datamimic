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

from datamimic_ce.authoring.diagnostics import Diagnostic, Severity
from datamimic_ce.authoring.rules.base import LintContext, Rule
from datamimic_ce.constants.data_type_constants import (
    DATA_TYPE_BINARY,
    DATA_TYPE_BOOL,
    DATA_TYPE_DECIMAL,
    DATA_TYPE_DICT,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_LIST,
    DATA_TYPE_STRING,
)
from datamimic_ce.constants.element_constants import (
    EL_COMMENT,
    EL_ID,
    EL_KEY,
    EL_NESTED_KEY,
    EL_SETUP,
    EL_VARIABLE,
)
from datamimic_ce.enums.distribution_enums import SourceDistribution

_DATA_TYPES = {
    DATA_TYPE_STRING,
    DATA_TYPE_INT,
    DATA_TYPE_FLOAT,
    DATA_TYPE_DECIMAL,
    DATA_TYPE_BOOL,
    DATA_TYPE_BINARY,
    DATA_TYPE_LIST,
    DATA_TYPE_DICT,
}
_DISTRIBUTIONS = {member.value for member in SourceDistribution}


class RootIsSetup(Rule):
    id = "DM106"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        root_tag = str(ctx.root.tag)
        if root_tag != EL_SETUP:
            yield ctx.diag(
                type(self),
                ctx.root,
                f"Root element must be <setup>, got <{root_tag}>.",
                "Wrap the descriptor in <setup> ... </setup>.",
            )


class UnknownElement(Rule):
    id = "DM101"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        known = ctx.schemas.tags
        for element in ctx.iter():
            tag = str(element.tag)
            if tag not in known:
                suggestion = difflib.get_close_matches(tag, sorted(known), n=1)
                hint = (
                    f"Did you mean <{suggestion[0]}>?"
                    if suggestion
                    else f"Known elements: {', '.join(sorted(known))}."
                )
                yield ctx.diag(type(self), element, f"Unknown element <{tag}>.", hint)


class InvalidChild(Rule):
    id = "DM102"
    severity = Severity.ERROR

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
                        f"<{child.tag}> is not allowed inside <{tag}>.",
                        f"<{tag}> accepts: {', '.join(sorted(schema.allowed_children))}.",
                    )


class LeafHasChildren(Rule):
    id = "DM107"
    severity = Severity.ERROR

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
                        f"<{tag}> does not accept any child elements (found <{child.tag}>).",
                        f"Remove <{child.tag}> or move it to a container element.",
                    )


class UnknownAttribute(Rule):
    id = "DM103"
    severity = Severity.ERROR

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
                    yield ctx.diag(type(self), element, f"Unknown attribute '{attr_name}' on <{tag}>.", hint)


class MissingRequiredAttribute(Rule):
    id = "DM104"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter():
            tag = str(element.tag)
            schema = ctx.schemas.get(tag)
            if schema is None or schema.model is None:
                continue
            for spec in schema.attributes.values():
                if spec.required and spec.name not in element.attrib:
                    yield ctx.diag(
                        type(self),
                        element,
                        f"<{tag}> is missing the required attribute '{spec.name}'.",
                        f'Add {spec.name}="..." to the <{tag}> element.',
                    )


class InvalidAttributeValue(Rule):
    id = "DM105"
    severity = Severity.ERROR

    def check(self, ctx: LintContext) -> Iterable[Diagnostic]:
        for element in ctx.iter():
            tag = str(element.tag)
            distribution = element.get("distribution")
            if distribution is not None and distribution not in _DISTRIBUTIONS:
                yield ctx.diag(
                    type(self),
                    element,
                    f"Invalid distribution '{distribution}'.",
                    f"Use one of: {', '.join(sorted(_DISTRIBUTIONS))}.",
                )
            if tag in (EL_KEY, EL_ID, EL_NESTED_KEY, EL_VARIABLE):
                type_value = element.get("type")
                if type_value is not None and type_value not in _DATA_TYPES:
                    yield ctx.diag(
                        type(self),
                        element,
                        f"Invalid type '{type_value}' on <{tag}>.",
                        f"Use one of: {', '.join(sorted(_DATA_TYPES))}.",
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
                        f"Attribute '{attr!s}' expects an integer, got '{value_str}'.",
                        f"Set {attr!s} to a whole number.",
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
