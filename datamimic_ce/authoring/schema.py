# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Machine-readable DSL schema, derived from the engine's own sources of truth.

- Attributes: Pydantic ``model_fields`` (name/alias/type/default/required)
- Elements:   ``model.element_registry`` (tag/model/parser/aliases/nesting)
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from pydantic import BaseModel

from datamimic_ce.model.constraints import (
    Constraint,
    element_constraints,
    rule_registry_revision,
    serialize_constraints,
)
from datamimic_ce.model.element_registry import (
    canonical_tag,
    get_model_class,
    get_valid_children,
    list_element_tags,
    registry_revision,
)


@dataclass(frozen=True)
class AttributeSpec:
    name: str  # XML attribute name (= field alias or field name)
    required: bool
    annotation: str  # rendered type, e.g. "int | None"
    default: object
    description: str | None = None  # from Field(description=...), when the model provides one


@dataclass(frozen=True)
class ElementSchema:
    tag: str
    model: type[BaseModel] | None
    attributes: dict[str, AttributeSpec]
    allowed_children: set[str] | None  # None = any children allowed; empty = leaf
    allowed_parents: set[str]  # derived by inverting the nesting table
    open_attrs: bool  # extra="allow" models (database/mongodb credentials)
    constraints: "tuple[Constraint, ...]" = ()  # from the model's __constraints__


class SchemaIndex:
    def __init__(self, elements: dict[str, ElementSchema]):
        self.elements = elements

    def get(self, tag: str) -> ElementSchema | None:
        return self.elements.get(tag)

    @property
    def tags(self) -> set[str]:
        return set(self.elements)


def _attribute_specs(model: type[BaseModel]) -> dict[str, AttributeSpec]:
    specs: dict[str, AttributeSpec] = {}
    for field_name, field in model.model_fields.items():
        xml_name = field.alias or field_name
        annotation_value = field.annotation
        annotation = (
            annotation_value.__name__
            if isinstance(annotation_value, type)
            else str(annotation_value)
        )
        specs[xml_name] = AttributeSpec(
            name=xml_name,
            required=field.is_required(),
            annotation=annotation.replace("typing.", ""),
            default=None if field.is_required() else field.default,
            description=field.description,
        )
    return specs


@lru_cache(maxsize=8)
def _build_schema_index(_element_revision: int, _rule_revision: int) -> SchemaIndex:
    # Invert the nesting table once: parent -> children becomes child -> parents.
    tags = list_element_tags()
    parents: dict[str, set[str]] = {tag: set() for tag in tags}
    children_map: dict[str, set[str] | None] = {}
    for tag in tags:
        allowed = get_valid_children(tag)
        children_map[tag] = set(allowed) if allowed is not None else None
        if allowed:
            for child in allowed:
                parents.setdefault(child, set()).add(tag)

    elements: dict[str, ElementSchema] = {}
    for tag in tags:
        model = get_model_class(tag)
        open_attrs = bool(model is not None and model.model_config.get("extra") == "allow")
        elements[tag] = ElementSchema(
            tag=tag,
            model=model,
            attributes=_attribute_specs(model) if model is not None else {},
            allowed_children=children_map.get(tag),
            allowed_parents=parents.get(tag, set()),
            open_attrs=open_attrs,
            constraints=element_constraints(tag),
        )
    return SchemaIndex(elements)


def build_schema_index() -> SchemaIndex:
    return _build_schema_index(registry_revision(), rule_registry_revision())


def element_json_schema(tag: str) -> dict[str, Any]:
    """The real Pydantic-derived JSON schema for an element's attribute model
    (BaseModel.model_json_schema()), carrying whatever description/examples the model's
    Field(...) definitions provide. This is the SPOT other schema consumers (scaffold.py's
    constrained-decoding spec, capabilities_manifest()) reflect from instead of hand-typing
    a parallel schema fragment."""
    schema = build_schema_index().get(canonical_tag(tag))
    if schema is None or schema.model is None:
        raise ValueError(f"'{tag}' has no attribute model to reflect a JSON schema from")
    result = schema.model.model_json_schema()
    constraints = element_constraints(tag)
    if constraints:
        result["constraints"] = serialize_constraints(constraints)
    else:
        result.pop("constraints", None)
    return result
