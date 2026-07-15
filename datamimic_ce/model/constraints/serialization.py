# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Constraint serialization: JSON-schema injectors and kind discriminators."""

from collections.abc import Callable
from typing import Any

# Attribute constants (imported at module level to avoid circular imports)
from datamimic_ce.model.constraints.types import (
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


def serialize_constraints(constraints: tuple[Constraint, ...]) -> list[dict[str, Any]]:
    """Serialize a tuple of constraints to a list of dicts with kind discriminators.

    Used by:
    - constraints_schema_extra: inject into Pydantic model JSON schemas
    - capabilities_manifest: expose constraints in the DSL reference
    - element_reference: render prose descriptions

    Each constraint becomes a dict with a "kind" discriminator and fact-specific fields.

    Args:
        constraints: A tuple of Constraint instances (from a model's __constraints__)

    Returns:
        A list of serialized constraint dicts, empty if constraints is empty
    """
    if not constraints:
        return []

    serialized: list[dict[str, Any]] = []
    for fact in constraints:
        serialized_fact: dict[str, Any] = {"kind": _constraint_kind(fact)}
        serialized_fact.update(_serialized_constraint_fields(fact))

        # Only serialize lint_only if True (non-default)
        if fact.lint_only:
            serialized_fact["lint_only"] = True

        # Only serialize message if present (non-default)
        if fact.message is not None:
            serialized_fact["message"] = fact.message

        serialized.append(serialized_fact)

    return serialized


def _serialized_constraint_fields(fact: Constraint) -> dict[str, Any]:
    if isinstance(fact, RequiredOneOf | MutuallyExclusive | AllOrNone):
        return {"attrs": sorted(fact.attrs)}
    if isinstance(fact, MutuallyExclusiveWhen):
        return {
            "when_attr": fact.when_attr,
            "attrs": sorted(fact.attrs),
            "when_true": fact.when_true,
        }
    if isinstance(fact, Requires):
        return {
            "attr": fact.attr,
            "needs": sorted(fact.needs),
            "when_true": fact.when_true,
        }
    if isinstance(fact, RequiresWhenValue):
        return {
            "when_attr": fact.when_attr,
            "when_values": sorted(fact.when_values),
            "needs": sorted(fact.needs),
            "unless": sorted(fact.unless),
        }
    if isinstance(fact, Forbids):
        return {
            "attr": fact.attr,
            "excludes": sorted(fact.excludes),
            "when_true": fact.when_true,
            "excludes_when_true": fact.excludes_when_true,
        }
    if isinstance(fact, ForbidsWhenValue):
        return {
            "when_attr": fact.when_attr,
            "when_values": sorted(fact.when_values),
            "excludes": sorted(fact.excludes),
        }
    if isinstance(fact, ValidValues):
        return {"attr": fact.attr, "values": sorted(resolved_values(fact))}
    if isinstance(fact, AllowedValuesWhen):
        return {
            "attr": fact.attr,
            "allowed": sorted(resolved_allowed(fact)),
            "when_attr": fact.when_attr,
            "when_true": fact.when_true,
        }
    raise TypeError(f"Unknown constraint type: {type(fact)}")


def constraints_schema_extra(
    constraints: tuple[Constraint, ...],
) -> Callable[[dict[str, Any]], None]:
    """Bind one explicit rule tuple to a Pydantic JSON-schema projector."""

    def inject(schema: dict[str, Any]) -> None:
        if constraints:
            schema["constraints"] = serialize_constraints(constraints)

    return inject


_CONSTRAINT_KIND_MAP: dict[type, str] = {
    RequiredOneOf: "required_one_of",
    MutuallyExclusive: "mutually_exclusive",
    MutuallyExclusiveWhen: "mutually_exclusive_when",
    Requires: "requires",
    RequiresWhenValue: "requires_when_value",
    AllOrNone: "all_or_none",
    Forbids: "forbids",
    ForbidsWhenValue: "forbids_when_value",
    ValidValues: "valid_values",
    AllowedValuesWhen: "allowed_values_when",
}


def _constraint_kind(fact: Constraint) -> str:
    """Map a constraint instance to its kind discriminator string."""
    kind = _CONSTRAINT_KIND_MAP.get(type(fact))
    if kind is not None:
        return kind
    raise TypeError(f"Unknown constraint type: {type(fact)}")
