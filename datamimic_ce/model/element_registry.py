# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Single registration owner for CE DSL elements.

An :class:`ElementDefinition` connects the four structural facts that otherwise
drift independently: tag/aliases, parser, attribute model, and valid children.
Runtime parser dispatch and authoring schema reflection are projections of this
registry; neither keeps its own element table.

Parser imports stay lazy because parser modules depend on models and
``ParserUtil``. Extensions register structure and constraints through one
atomic API; built-in definitions remain immutable.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel

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

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

    from datamimic_ce.model.constraints.types import Constraint
    from datamimic_ce.parsers.statement_parser import StatementParser


class ParserFactory(Protocol):
    """Constructor contract shared by every registry-dispatchable parser."""

    def __call__(self, element: Element, properties: dict, /) -> StatementParser: ...


@dataclass(frozen=True)
class ElementDefinition:
    """Machine-readable definition of one canonical DSL element."""

    tag: str
    model: type[BaseModel] | None
    parser: ParserFactory | None
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
    """Build built-in definitions lazily to avoid model/parser import cycles."""
    from datamimic_ce.model.array_model import ArrayModel
    from datamimic_ce.model.assert_model import AssertModel
    from datamimic_ce.model.database_model import DatabaseModel
    from datamimic_ce.model.demographics_model import DemographicsModel
    from datamimic_ce.model.element_model import ElementModel
    from datamimic_ce.model.else_if_model import ElseIfModel
    from datamimic_ce.model.execute_model import ExecuteModel
    from datamimic_ce.model.generate_model import GenerateModel
    from datamimic_ce.model.generator_model import GeneratorModel
    from datamimic_ce.model.if_model import IfModel
    from datamimic_ce.model.include_model import IncludeModel
    from datamimic_ce.model.item_model import ItemModel
    from datamimic_ce.model.key_model import KeyModel
    from datamimic_ce.model.list_model import ListModel
    from datamimic_ce.model.memstore_model import MemstoreModel
    from datamimic_ce.model.mongodb_model import MongoDBModel
    from datamimic_ce.model.nested_key_model import NestedKeyModel
    from datamimic_ce.model.reference_field_model import ReferenceFieldModel
    from datamimic_ce.model.reference_model import ReferenceModel
    from datamimic_ce.model.setup_model import SetupModel
    from datamimic_ce.model.state_machine_model import StateMachineModel
    from datamimic_ce.model.value_model import ValueModel
    from datamimic_ce.model.variable_model import VariableModel
    from datamimic_ce.model.while_model import WhileModel
    from datamimic_ce.parsers.array_parser import ArrayParser
    from datamimic_ce.parsers.assert_parser import AssertParser
    from datamimic_ce.parsers.condition_parser import ConditionParser
    from datamimic_ce.parsers.database_parser import DatabaseParser
    from datamimic_ce.parsers.demographics_parser import DemographicsParser
    from datamimic_ce.parsers.echo_parser import EchoParser
    from datamimic_ce.parsers.element_parser import ElementParser
    from datamimic_ce.parsers.else_if_parser import ElseIfParser
    from datamimic_ce.parsers.else_parser import ElseParser
    from datamimic_ce.parsers.execute_parser import ExecuteParser
    from datamimic_ce.parsers.generate_parser import GenerateParser
    from datamimic_ce.parsers.generator_parser import GeneratorParser
    from datamimic_ce.parsers.if_parser import IfParser
    from datamimic_ce.parsers.include_parser import IncludeParser
    from datamimic_ce.parsers.item_parser import ItemParser
    from datamimic_ce.parsers.key_parser import KeyParser
    from datamimic_ce.parsers.list_parser import ListParser
    from datamimic_ce.parsers.memstore_parser import MemstoreParser
    from datamimic_ce.parsers.mongodb_parser import MongoDBParser
    from datamimic_ce.parsers.nested_key_parser import NestedKeyParser
    from datamimic_ce.parsers.reference_parser import ReferenceParser
    from datamimic_ce.parsers.state_machine_parser import StateMachineParser
    from datamimic_ce.parsers.variable_parser import VariableParser
    from datamimic_ce.parsers.while_parser import WhileParser

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
            GenerateParser,
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
            KeyParser,
            frozenset({EL_ELEMENT}),
            frozenset({EL_ID}),
        ),
        ElementDefinition(EL_VARIABLE, VariableModel, VariableParser),
        ElementDefinition(
            EL_NESTED_KEY,
            NestedKeyModel,
            NestedKeyParser,
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
        ElementDefinition(EL_ARRAY, ArrayModel, ArrayParser, frozenset({EL_VALUE})),
        # Child-only elements have models for authoring but no standalone parser.
        ElementDefinition(EL_VALUE, ValueModel, None),
        ElementDefinition(EL_LIST, ListModel, ListParser, frozenset({EL_ITEM})),
        ElementDefinition(
            EL_ITEM,
            ItemModel,
            ItemParser,
            frozenset({EL_KEY, EL_ID, EL_NESTED_KEY, EL_LIST, EL_ARRAY, EL_ELEMENT}),
        ),
        ElementDefinition(EL_REFERENCE, ReferenceModel, ReferenceParser, frozenset({EL_FIELD})),
        ElementDefinition(EL_FIELD, ReferenceFieldModel, None),
        ElementDefinition(EL_INCLUDE, IncludeModel, IncludeParser, frozenset({EL_SETUP})),
        ElementDefinition(EL_MEMSTORE, MemstoreModel, MemstoreParser),
        ElementDefinition(EL_EXECUTE, ExecuteModel, ExecuteParser),
        ElementDefinition(EL_DATABASE, DatabaseModel, DatabaseParser),
        ElementDefinition(EL_MONGODB, MongoDBModel, MongoDBParser),
        ElementDefinition(EL_IF, IfModel, IfParser, None),
        ElementDefinition(EL_ELSE_IF, ElseIfModel, ElseIfParser, None),
        ElementDefinition(EL_ELSE, None, ElseParser, None),
        ElementDefinition(EL_CONDITION, None, ConditionParser, frozenset({EL_IF, EL_ELSE_IF, EL_ELSE})),
        ElementDefinition(EL_ECHO, None, EchoParser),
        ElementDefinition(EL_ELEMENT, ElementModel, ElementParser),
        ElementDefinition(EL_GENERATOR, GeneratorModel, GeneratorParser),
        ElementDefinition(EL_DEMOGRAPHICS, DemographicsModel, DemographicsParser),
        ElementDefinition(
            EL_STATE_MACHINE,
            StateMachineModel,
            StateMachineParser,
            frozenset({EL_TRANSITION}),
        ),
        ElementDefinition(EL_TRANSITION, None, None),
        ElementDefinition(EL_WHILE, WhileModel, WhileParser, None),
        ElementDefinition(EL_ASSERT, AssertModel, AssertParser),
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
    from datamimic_ce.model.constraints.registry import (
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
    from datamimic_ce.model.constraints.registry import (
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


def get_parser_class(tag: str) -> ParserFactory | None:
    definition = get_element_definition(tag)
    return definition.parser if definition is not None else None


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
