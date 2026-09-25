"""Schema facts consumed by lint rules and populated by the DSL projection."""

from dataclasses import dataclass

from pydantic import BaseModel

from datamimic_ce.engine.dsl.api import Constraint


@dataclass(frozen=True)
class AttributeSpec:
    name: str
    required: bool
    annotation: str
    default: object
    description: str | None = None


@dataclass(frozen=True)
class ElementSchema:
    tag: str
    model: type[BaseModel] | None
    attributes: dict[str, AttributeSpec]
    allowed_children: set[str] | None
    allowed_parents: set[str]
    open_attrs: bool
    constraints: tuple[Constraint, ...] = ()


class SchemaIndex:
    def __init__(self, elements: dict[str, ElementSchema]):
        self.elements = elements

    def get(self, tag: str) -> ElementSchema | None:
        return self.elements.get(tag)

    @property
    def tags(self) -> set[str]:
        return set(self.elements)
