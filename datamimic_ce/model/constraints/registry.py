# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Element-rule registry: the SPOT that maps CE DSL tag names to their Constraint tuples."""

# Attribute constants (imported at module level to avoid circular imports)
from datamimic_ce.constants.element_constants import (
    EL_ARRAY,
    EL_ASSERT,
    EL_CONDITION,
    EL_DATABASE,
    EL_DEMOGRAPHICS,
    EL_ECHO,
    EL_ELEMENT,
    EL_ELSE,
    EL_ELSE_IF,
    EL_EXECUTE,
    EL_FIELD,
    EL_GENERATE,
    EL_GENERATOR,
    EL_ID,
    EL_IF,
    EL_INCLUDE,
    EL_ITEM,
    EL_ITERATE,
    EL_KEY,
    EL_LIST,
    EL_MEMSTORE,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_REFERENCE,
    EL_SETUP,
    EL_STATE_MACHINE,
    EL_TRANSITION,
    EL_VALUE,
    EL_VARIABLE,
    EL_WHILE,
)
from datamimic_ce.model.constraints.facts import (
    _ARRAY_RULES,
    _EXECUTE_RULES,
    _GENERATE_RULES,
    _KEY_RULES,
    _NESTED_KEY_RULES,
    _REFERENCE_RULES,
    _VARIABLE_RULES,
    ITERATE_REQUIRES_SOURCE,
)
from datamimic_ce.model.constraints.types import Constraint

# Explicit entry for every CE registry tag. Empty tuples are intentional and make
# omissions review-visible: a new built-in element must decide its rule contract.
_ELEMENT_CONSTRAINTS: dict[str, tuple[Constraint, ...]] = {
    EL_SETUP: (),
    EL_GENERATE: _GENERATE_RULES,
    EL_ITERATE: (*_GENERATE_RULES, ITERATE_REQUIRES_SOURCE),
    EL_KEY: _KEY_RULES,
    EL_ID: _KEY_RULES,
    EL_ELEMENT: _KEY_RULES,
    EL_VARIABLE: _VARIABLE_RULES,
    EL_NESTED_KEY: _NESTED_KEY_RULES,
    EL_ARRAY: _ARRAY_RULES,
    EL_VALUE: (),
    EL_LIST: (),
    EL_ITEM: (),
    EL_REFERENCE: _REFERENCE_RULES,
    EL_FIELD: (),
    EL_INCLUDE: (),
    EL_MEMSTORE: (),
    EL_EXECUTE: _EXECUTE_RULES,
    EL_DATABASE: (),
    EL_MONGODB: (),
    EL_IF: (),
    EL_ELSE_IF: (),
    EL_ELSE: (),
    EL_CONDITION: (),
    EL_ECHO: (),
    EL_GENERATOR: (),
    EL_DEMOGRAPHICS: (),
    EL_STATE_MACHINE: (),
    EL_TRANSITION: (),
    EL_WHILE: (),
    EL_ASSERT: (),
}

_EXTENSION_CONSTRAINTS: dict[str, tuple[Constraint, ...]] = {}
_RULE_REGISTRY_REVISION = 0


def element_constraints(tag: str) -> tuple[Constraint, ...]:
    """Return the centrally registered rule facts for one CE DSL tag."""
    return _EXTENSION_CONSTRAINTS.get(tag, _ELEMENT_CONSTRAINTS.get(tag, ()))


def _register_element_constraints(tag: str, constraints: tuple[Constraint, ...]) -> None:
    """Register one part of an atomic extension contract."""
    global _RULE_REGISTRY_REVISION

    if tag in _ELEMENT_CONSTRAINTS or tag in _EXTENSION_CONSTRAINTS:
        raise ValueError(f"business-rule contract for <{tag}> is already registered")
    _EXTENSION_CONSTRAINTS[tag] = constraints
    _RULE_REGISTRY_REVISION += 1


def _unregister_element_constraints(tag: str) -> None:
    """Remove one part of an atomic extension contract."""
    global _RULE_REGISTRY_REVISION

    if tag not in _EXTENSION_CONSTRAINTS:
        raise KeyError(f"extension business-rule contract for <{tag}> is not registered")
    del _EXTENSION_CONSTRAINTS[tag]
    _RULE_REGISTRY_REVISION += 1


def rule_registry_revision() -> int:
    """Return a monotonic revision used by authoring projections."""
    return _RULE_REGISTRY_REVISION


def registered_rule_tags() -> frozenset[str]:
    """Tags with an explicit rule-registry decision, including intentional empties."""
    return frozenset((*_ELEMENT_CONSTRAINTS, *_EXTENSION_CONSTRAINTS))
