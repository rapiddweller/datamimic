# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Canonical CE DSL element facts for parsing and authoring.

Parser implementations are bound by the parsing layer. Extensions register
structure and constraints atomically; built-in definitions remain immutable.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

from pydantic import BaseModel

from datamimic_ce.engine.dsl.constants.element_constants import (
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

if TYPE_CHECKING:
    from datamimic_ce.engine.dsl.model.constraints.types import Constraint


@dataclass(frozen=True)
class ElementDefinition:
    """Machine-readable definition of one canonical DSL element."""

    tag: str
    model: type[BaseModel] | None
    parser: Callable[..., object] | None
    allowed_children: frozenset[str] | None = frozenset()
    aliases: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.tag:
            raise ValueError("element tag must not be empty")
        if self.tag in self.aliases:
            raise ValueError(f"canonical element tag <{self.tag}> cannot alias itself")
        if self.allowed_children is not None:
            object.__setattr__(self, "allowed_children", frozenset(self.allowed_children))
        object.__setattr__(self, "aliases", frozenset(self.aliases))


@lru_cache(maxsize=1)
def _builtin_definitions() -> dict[str, ElementDefinition]:
    """Build built-in grammar facts without importing parsing implementations."""
    from datamimic_ce.engine.dsl.model.array_model import ArrayModel
    from datamimic_ce.engine.dsl.model.assert_model import AssertModel
    from datamimic_ce.engine.dsl.model.database_model import DatabaseModel
    from datamimic_ce.engine.dsl.model.demographics_model import DemographicsModel
    from datamimic_ce.engine.dsl.model.element_model import ElementModel
    from datamimic_ce.engine.dsl.model.else_if_model import ElseIfModel
    from datamimic_ce.engine.dsl.model.execute_model import ExecuteModel
    from datamimic_ce.engine.dsl.model.generate_model import GenerateModel
    from datamimic_ce.engine.dsl.model.generator_model import GeneratorModel
    from datamimic_ce.engine.dsl.model.if_model import IfModel
    from datamimic_ce.engine.dsl.model.include_model import IncludeModel
    from datamimic_ce.engine.dsl.model.item_model import ItemModel
    from datamimic_ce.engine.dsl.model.key_model import KeyModel
    from datamimic_ce.engine.dsl.model.list_model import ListModel
    from datamimic_ce.engine.dsl.model.memstore_model import MemstoreModel
    from datamimic_ce.engine.dsl.model.mongodb_model import MongoDBModel
    from datamimic_ce.engine.dsl.model.nested_key_model import NestedKeyModel
    from datamimic_ce.engine.dsl.model.reference_field_model import ReferenceFieldModel
    from datamimic_ce.engine.dsl.model.reference_model import ReferenceModel
    from datamimic_ce.engine.dsl.model.setup_model import SetupModel
    from datamimic_ce.engine.dsl.model.state_machine_model import StateMachineModel
    from datamimic_ce.engine.dsl.model.value_model import ValueModel
    from datamimic_ce.engine.dsl.model.variable_model import VariableModel
    from datamimic_ce.engine.dsl.model.while_model import WhileModel

    definitions = (
        # <setup> is parsed by DescriptorParser directly, so it has no child-dispatch parser.
        ElementDefinition(
            EL_SETUP,
            SetupModel,
            None,
            frozenset(
                {
                    EL_MONGODB,
                    EL_GENERATE,
                    EL_ITERATE,
                    EL_DATABASE,
                    EL_INCLUDE,
                    EL_MEMSTORE,
                    EL_EXECUTE,
                    EL_ECHO,
                    EL_VARIABLE,
                    EL_GENERATOR,
                    EL_DEMOGRAPHICS,
                    EL_STATE_MACHINE,
                    EL_ASSERT,
                }
            ),
        ),
        ElementDefinition(
            EL_GENERATE,
            GenerateModel,
            None,
            frozenset(
                {
                    EL_GENERATE,
                    EL_ITERATE,
                    EL_KEY,
                    EL_ID,
                    EL_VARIABLE,
                    EL_REFERENCE,
                    EL_NESTED_KEY,
                    EL_LIST,
                    EL_ARRAY,
                    EL_ECHO,
                    EL_CONDITION,
                    EL_WHILE,
                    EL_INCLUDE,
                    EL_ASSERT,
                }
            ),
            frozenset({EL_ITERATE}),
        ),
        ElementDefinition(
            EL_KEY,
            KeyModel,
            None,
            frozenset({EL_ELEMENT}),
            frozenset({EL_ID}),
        ),
        ElementDefinition(EL_VARIABLE, VariableModel, None),
        ElementDefinition(
            EL_NESTED_KEY,
            NestedKeyModel,
            None,
            frozenset(
                {
                    EL_KEY,
                    EL_ID,
                    EL_VARIABLE,
                    EL_NESTED_KEY,
                    EL_EXECUTE,
                    EL_LIST,
                    EL_ECHO,
                    EL_ELEMENT,
                    EL_ARRAY,
                    EL_CONDITION,
                    EL_WHILE,
                    EL_ASSERT,
                }
            ),
        ),
        ElementDefinition(EL_ARRAY, ArrayModel, None, frozenset({EL_VALUE})),
        # Child-only elements have models for authoring but no standalone parser.
        ElementDefinition(EL_VALUE, ValueModel, None),
        ElementDefinition(EL_LIST, ListModel, None, frozenset({EL_ITEM})),
        ElementDefinition(
            EL_ITEM,
            ItemModel,
            None,
            frozenset({EL_KEY, EL_ID, EL_NESTED_KEY, EL_LIST, EL_ARRAY, EL_ELEMENT}),
        ),
        ElementDefinition(EL_REFERENCE, ReferenceModel, None, frozenset({EL_FIELD})),
        ElementDefinition(EL_FIELD, ReferenceFieldModel, None),
        ElementDefinition(EL_INCLUDE, IncludeModel, None, frozenset({EL_SETUP})),
        ElementDefinition(EL_MEMSTORE, MemstoreModel, None),
        ElementDefinition(EL_EXECUTE, ExecuteModel, None),
        ElementDefinition(EL_DATABASE, DatabaseModel, None),
        ElementDefinition(EL_MONGODB, MongoDBModel, None),
        ElementDefinition(EL_IF, IfModel, None, None),
        ElementDefinition(EL_ELSE_IF, ElseIfModel, None, None),
        ElementDefinition(EL_ELSE, None, None, None),
        ElementDefinition(EL_CONDITION, None, None, frozenset({EL_IF, EL_ELSE_IF, EL_ELSE})),
        ElementDefinition(EL_ECHO, None, None),
        ElementDefinition(EL_ELEMENT, ElementModel, None),
        ElementDefinition(EL_GENERATOR, GeneratorModel, None),
        ElementDefinition(EL_DEMOGRAPHICS, DemographicsModel, None),
        ElementDefinition(
            EL_STATE_MACHINE,
            StateMachineModel,
            None,
            frozenset({EL_TRANSITION}),
        ),
        ElementDefinition(EL_TRANSITION, None, None),
        ElementDefinition(EL_WHILE, WhileModel, None, None),
        ElementDefinition(EL_ASSERT, AssertModel, None),
    )
    return {definition.tag: definition for definition in definitions}


_extension_definitions: dict[str, ElementDefinition] = {}
_registry_revision = 0


def _definitions() -> dict[str, ElementDefinition]:
    return {**_builtin_definitions(), **_extension_definitions}


def _alias_map() -> dict[str, str]:
    return {alias: definition.tag for definition in _definitions().values() for alias in definition.aliases}


def registry_revision() -> int:
    """Return a monotonic revision used by derived-schema caches."""
    return _registry_revision


def _register_element_definition(definition: ElementDefinition) -> None:
    """Register the structural half of an extension contract."""
    global _registry_revision

    occupied = set(_definitions()) | set(_alias_map())
    requested = {definition.tag, *definition.aliases}
    conflicts = occupied & requested
    if conflicts:
        rendered = ", ".join(f"<{tag}>" for tag in sorted(conflicts))
        raise ValueError(f"element tag or alias already registered: {rendered}")
    _extension_definitions[definition.tag] = definition
    _registry_revision += 1


def _unregister_element_definition(tag: str) -> None:
    """Remove the structural half of an extension contract."""
    global _registry_revision

    canonical = canonical_tag(tag)
    if canonical not in _extension_definitions:
        raise KeyError(f"extension element <{tag}> is not registered")
    del _extension_definitions[canonical]
    _registry_revision += 1


def register_element_extension(
    definition: ElementDefinition,
    constraints: tuple[Constraint, ...] = (),
) -> None:
    """Atomically register structure and business rules for one extension element."""
    from datamimic_ce.engine.dsl.model.constraints.registry import (
        _register_element_constraints,
        _unregister_element_constraints,
    )

    _register_element_definition(definition)
    registered_rule_tags: list[str] = []
    try:
        for tag in (definition.tag, *sorted(definition.aliases)):
            _register_element_constraints(tag, constraints)
            registered_rule_tags.append(tag)
    except Exception:
        for tag in reversed(registered_rule_tags):
            _unregister_element_constraints(tag)
        _unregister_element_definition(definition.tag)
        raise


def unregister_element_extension(tag: str) -> None:
    """Atomically remove structure and business rules for one extension element."""
    from datamimic_ce.engine.dsl.model.constraints.registry import (
        _register_element_constraints,
        _unregister_element_constraints,
        element_constraints,
    )

    definition = get_element_definition(tag)
    canonical = canonical_tag(tag)
    if definition is None or canonical not in _extension_definitions:
        raise KeyError(f"extension element <{tag}> is not registered")

    contracts = {
        registered_tag: element_constraints(registered_tag)
        for registered_tag in (definition.tag, *sorted(definition.aliases))
    }
    removed: list[str] = []
    try:
        for registered_tag in contracts:
            _unregister_element_constraints(registered_tag)
            removed.append(registered_tag)
        _unregister_element_definition(canonical)
    except Exception:
        for registered_tag in removed:
            _register_element_constraints(registered_tag, contracts[registered_tag])
        raise


def canonical_tag(tag: str) -> str:
    """Resolve an authoring alias to its canonical runtime tag."""
    return _alias_map().get(tag, tag)


def element_aliases() -> dict[str, str]:
    """Return a snapshot of alias-to-canonical mappings."""
    return _alias_map()


def list_element_tags() -> list[str]:
    """List canonical, alias, model-less, and child-only element tags."""
    result: list[str] = []
    for definition in _definitions().values():
        result.append(definition.tag)
        result.extend(sorted(definition.aliases))
    return result


def get_element_definition(tag: str) -> ElementDefinition | None:
    """Return the canonical definition for a tag or alias."""
    return _definitions().get(canonical_tag(tag))


def get_model_class(tag: str) -> type[BaseModel] | None:
    definition = get_element_definition(tag)
    return definition.model if definition is not None else None


def get_valid_children(tag: str) -> set[str] | None:
    """Return ``None`` for unrestricted, a set for restricted/leaf elements."""
    definition = get_element_definition(tag)
    if definition is None:
        return set()
    children = definition.allowed_children
    return None if children is None else set(children)
