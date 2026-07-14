# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Machine-readable DSL schema, derived from the engine's own sources of truth.

- Attributes: Pydantic ``model_fields`` (name/alias/type/default/required)
- Nesting:    ``ParserUtil.get_valid_sub_elements_set_by_tag``
- Tags:       ``element_constants``

The one table the engine lacks is the element→model map below; a gate test
(tests_ce/unit_tests/test_authoring/test_schema_index.py) reconciles it against
the real parser dispatch so it cannot drift.
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

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
from datamimic_ce.model.array_model import ArrayModel
from datamimic_ce.model.assert_model import AssertModel
from datamimic_ce.model.constraints import Constraint
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
from datamimic_ce.parsers.parser_util import ParserUtil

# Element tag -> attribute model. None = structural/text element without attribute schema
# (<condition>/<else> carry no validated attributes; <echo> is text; <transition> is
# validated inside <state-machine>; <comment> is a no-op and not dispatchable content here).
ELEMENT_MODEL_MAP: dict[str, type[BaseModel] | None] = {
    EL_SETUP: SetupModel,
    EL_GENERATE: GenerateModel,
    EL_ITERATE: GenerateModel,  # alias
    EL_KEY: KeyModel,
    EL_ID: KeyModel,  # alias
    EL_VARIABLE: VariableModel,
    EL_NESTED_KEY: NestedKeyModel,
    EL_ARRAY: ArrayModel,
    EL_VALUE: ValueModel,  # <array type="literal"> child only
    EL_LIST: ListModel,
    EL_ITEM: ItemModel,
    EL_REFERENCE: ReferenceModel,
    EL_FIELD: ReferenceFieldModel,
    EL_INCLUDE: IncludeModel,
    EL_MEMSTORE: MemstoreModel,
    EL_EXECUTE: ExecuteModel,
    EL_DATABASE: DatabaseModel,
    EL_MONGODB: MongoDBModel,
    EL_IF: IfModel,
    EL_ELSE_IF: ElseIfModel,
    EL_ELSE: None,
    EL_CONDITION: None,
    EL_ECHO: None,
    EL_ELEMENT: ElementModel,
    EL_GENERATOR: GeneratorModel,
    EL_DEMOGRAPHICS: DemographicsModel,
    EL_STATE_MACHINE: StateMachineModel,
    EL_TRANSITION: None,
    EL_WHILE: WhileModel,
    EL_ASSERT: AssertModel,
}

# Tags accepted as <generate>/<key> aliases map onto the same schema (attributes AND
# nesting rules); expose canonical names.
ALIASES: dict[str, str] = {EL_ITERATE: EL_GENERATE, EL_ID: EL_KEY}


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
        annotation = getattr(field.annotation, "__name__", None) or str(field.annotation)
        specs[xml_name] = AttributeSpec(
            name=xml_name,
            required=field.is_required(),
            annotation=annotation.replace("typing.", ""),
            default=None if field.is_required() else field.default,
            description=field.description,
        )
    return specs


@lru_cache(maxsize=1)
def build_schema_index() -> SchemaIndex:
    # Invert the nesting table once: parent -> children becomes child -> parents.
    parents: dict[str, set[str]] = {tag: set() for tag in ELEMENT_MODEL_MAP}
    children_map: dict[str, set[str] | None] = {}
    for tag in ELEMENT_MODEL_MAP:
        # aliases (<iterate>/<id>) share the canonical element's nesting rules —
        # the engine normalizes via the statement TYPE, so the raw-tag lookup would miss
        allowed = ParserUtil.get_valid_sub_elements_set_by_tag(ALIASES.get(tag, tag))
        children_map[tag] = set(allowed) if allowed is not None else None
        if allowed:
            for child in allowed:
                parents.setdefault(child, set()).add(tag)

    elements: dict[str, ElementSchema] = {}
    for tag, model in ELEMENT_MODEL_MAP.items():
        open_attrs = bool(model is not None and model.model_config.get("extra") == "allow")
        elements[tag] = ElementSchema(
            tag=tag,
            model=model,
            attributes=_attribute_specs(model) if model is not None else {},
            allowed_children=children_map.get(tag),
            allowed_parents=parents.get(tag, set()),
            open_attrs=open_attrs,
            constraints=getattr(model, "__constraints__", ()) if model is not None else (),
        )
    return SchemaIndex(elements)


def element_json_schema(tag: str) -> dict[str, Any]:
    """The real Pydantic-derived JSON schema for an element's attribute model
    (BaseModel.model_json_schema()), carrying whatever description/examples the model's
    Field(...) definitions provide. This is the SPOT other schema consumers (scaffold.py's
    constrained-decoding spec, capabilities_manifest()) reflect from instead of hand-typing
    a parallel schema fragment."""
    schema = build_schema_index().get(ALIASES.get(tag, tag))
    if schema is None or schema.model is None:
        raise ValueError(f"'{tag}' has no attribute model to reflect a JSON schema from")
    return schema.model.model_json_schema()
