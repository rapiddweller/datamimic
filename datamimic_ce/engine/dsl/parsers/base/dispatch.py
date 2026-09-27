"""Dispatch XML elements to built-in or registered extension parsers."""

import copy
import re
from collections.abc import Callable
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader
from datamimic_ce.engine.dsl.parsers.input.properties import parse_properties
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement, xml_tag
from datamimic_ce.engine.dsl.statements.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.statements.condition_statement import ConditionStatement
from datamimic_ce.engine.dsl.statements.flow.loops.while_statement import WhileStatement
from datamimic_ce.engine.dsl.statements.generate_statement import GenerateStatement
from datamimic_ce.engine.dsl.statements.setup.include_statement import IncludeStatement
from datamimic_ce.engine.dsl.statements.setup.setup_statement import SetupStatement
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.statements.values.structured.array_statement import ArrayStatement
from datamimic_ce.engine.dsl.statements.values.structured.nested_key_statement import NestedKeyStatement
from datamimic_ce.engine.dsl.vocabulary.constants import element_constants as tags
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import (
    EL_ARRAY,
    EL_COMMENT,
    EL_CONDITION,
    EL_DATABASE,
    EL_GENERATE,
    EL_MONGODB,
    EL_NESTED_KEY,
    EL_SETUP,
    EL_WHILE,
)

BUILTIN_PARSERS: dict[str, Callable[..., object]] = {}


@runtime_checkable
class _Parser(Protocol):
    def parse(self, *args: object, **kwargs: object) -> Statement: ...

    def set_runtime_environment(self, value: Literal["development", "production"]) -> None: ...


def get_element_tag_by_statement(stmt: Statement) -> str:
    if isinstance(stmt, ArrayStatement):
        return EL_ARRAY
    elif isinstance(stmt, ConditionStatement):
        return EL_CONDITION
    elif isinstance(stmt, SetupStatement):
        return EL_SETUP
    elif isinstance(stmt, NestedKeyStatement):
        return EL_NESTED_KEY
    elif isinstance(stmt, GenerateStatement):
        return EL_GENERATE
    elif isinstance(stmt, WhileStatement):
        return EL_WHILE
    raise ValueError(f"Cannot get element tag for statement {stmt.__class__.__name__}")


def get_valid_sub_elements_set_by_tag(ele_tag: str) -> set[str] | None:
    from datamimic_ce.engine.dsl.model.registry import get_valid_children

    return get_valid_children(ele_tag)


def get_parser_by_element(
    element: XmlElement,
    properties: dict[str, str],
    runtime_environment: Literal["development", "production"] = "production",
) -> _Parser:
    from datamimic_ce.engine.dsl.model.registry import canonical_tag, get_element_definition

    tag = xml_tag(element)
    definition = get_element_definition(tag)
    canonical = canonical_tag(tag)
    parser_class = None if definition is None else definition.parser or BUILTIN_PARSERS.get(canonical)
    if parser_class is None:
        raise ValueError(f"Cannot get parser for element <{tag}>")
    parser = parser_class(element, properties)
    if not isinstance(parser, _Parser):
        raise TypeError(f"Parser for element <{tag}> does not implement the parser contract")
    if tag in {EL_DATABASE, EL_MONGODB}:
        parser.set_runtime_environment(runtime_environment)
    return parser


def parse_sub_elements(
    descriptor_dir: Path,
    element: XmlElement,
    properties: dict[str, str] | None,
    parent_stmt: Statement,
    runtime_environment: Literal["development", "production"] = "production",
    *,
    profile_loader: ConnectionProfileLoader,
) -> list[Statement]:
    from datamimic_ce.engine.dsl.model.registry import canonical_tag

    result: list[Statement] = []
    copied_props = copy.deepcopy(properties) if properties else {}

    for child_ele in element:
        child_tag = xml_tag(child_ele)
        if child_tag == EL_COMMENT:
            continue
        parser = get_parser_by_element(child_ele, copied_props, runtime_environment)
        canonical = canonical_tag(child_tag)
        profile_kwargs: dict[str, object] = (
            {"profile_loader": profile_loader}
            if canonical
            in {
                EL_GENERATE,
                EL_NESTED_KEY,
                tags.EL_KEY,
                tags.EL_ITEM,
                tags.EL_LIST,
                EL_CONDITION,
                EL_WHILE,
                tags.EL_IF,
                tags.EL_ELSE_IF,
                tags.EL_ELSE,
                EL_DATABASE,
                EL_MONGODB,
            }
            else {}
        )
        if canonical in {EL_GENERATE, EL_NESTED_KEY, tags.EL_VARIABLE, tags.EL_ELEMENT}:
            if canonical == tags.EL_VARIABLE and xml_tag(element) == EL_SETUP:
                stmt = parser.parse(parent_stmt=parent_stmt, has_parent_setup=True)
            elif canonical in {EL_GENERATE, EL_NESTED_KEY}:
                stmt = parser.parse(descriptor_dir=descriptor_dir, parent_stmt=parent_stmt, **profile_kwargs)
            else:
                stmt = parser.parse(parent_stmt=parent_stmt)
        elif canonical in {
            tags.EL_MEMSTORE,
            tags.EL_EXECUTE,
            tags.EL_INCLUDE,
            EL_ARRAY,
            tags.EL_ECHO,
            tags.EL_GENERATOR,
            tags.EL_STATE_MACHINE,
            tags.EL_ASSERT,
        }:
            stmt = parser.parse()
        elif canonical == tags.EL_REFERENCE:
            stmt = parser.parse(parent_stmt=parent_stmt)
        elif canonical == tags.EL_KEY:
            stmt = parser.parse(descriptor_dir=descriptor_dir, parent_stmt=parent_stmt, **profile_kwargs)
        elif canonical in {tags.EL_ITEM, tags.EL_LIST}:
            stmt = parser.parse(descriptor_dir=descriptor_dir, **profile_kwargs)
        elif canonical in {EL_CONDITION, EL_WHILE}:
            if not isinstance(parent_stmt, CompositeStatement):
                raise TypeError(f"<{child_tag}> requires a composite parent statement")
            stmt = parser.parse(descriptor_dir=descriptor_dir, parent_stmt=parent_stmt, **profile_kwargs)
        elif canonical in {tags.EL_IF, tags.EL_ELSE_IF, tags.EL_ELSE}:
            if not isinstance(parent_stmt, ConditionStatement):
                raise TypeError(f"<{child_tag}> requires a condition parent statement")
            stmt = parser.parse(descriptor_dir=descriptor_dir, parent_stmt=parent_stmt, **profile_kwargs)
        elif canonical in {EL_DATABASE, EL_MONGODB}:
            stmt = parser.parse(descriptor_dir=descriptor_dir, **profile_kwargs)
        else:
            stmt = parser.parse(descriptor_dir=descriptor_dir)

        if stmt is None:
            raise ValueError(f"Cannot parse element <{child_tag}>")

        if isinstance(stmt, IncludeStatement):
            uri: str = stmt.uri
            if "{" not in uri and uri.endswith(".properties"):
                copied_props.update(parse_properties(descriptor_dir / uri))

        result.append(stmt)

    return result


def retrieve_element_attributes(attributes: dict[str, object], properties: dict[str, str] | None) -> dict[str, object]:
    if properties is None:
        return attributes

    for key, value in attributes.items():
        if type(value) is str and re.match(r"^\{[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]+)*\}$", value) is not None:
            prop_key = value[1:-1]
            if "." not in prop_key:
                attributes[key] = properties.get(prop_key, value)
            else:
                temp_value: dict | None = copy.deepcopy(properties)
                for key_part in prop_key.split("."):
                    if temp_value:
                        temp_value = temp_value.get(key_part)
                    if temp_value is None:
                        break
                attributes[key] = temp_value or value

    return attributes
