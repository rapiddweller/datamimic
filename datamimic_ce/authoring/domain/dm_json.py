# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Runtime-free transport values for the canonical agent-only DM JSON document."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final, Literal

from pydantic import (
    Field,
    JsonValue,
    SerializerFunctionWrapHandler,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    ValidationError,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
)
from pydantic_core import PydanticCustomError

from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_SETUP
from datamimic_ce.engine.dsl.vocabulary.contracts.dsl_element import ElementContentModeKind

from .common import AuthoringModel, NonEmptyStrictStr

DmJsonScalar = StrictStr | StrictInt | StrictFloat | StrictBool
DM_JSON_TRAVERSAL_COUNT: Final = "traversal_count"
DM_JSON_TRAVERSAL_LIMIT: Final = "traversal_limit"


class DmJsonCodecError(ValueError):
    """A fail-closed codec rejection with an exact public document path."""

    def __init__(
        self,
        message: str,
        *,
        path: tuple[str | int, ...] = (),
        expected: JsonValue | None = None,
        actual: JsonValue | None = None,
        remediation: str | None = None,
    ) -> None:
        super().__init__(message)
        self.path = path
        self.expected = expected
        self.actual = actual
        self.remediation = remediation


class DmJsonContentV1(AuthoringModel):
    """One closed non-attribute content form for an XML element."""

    kind: ElementContentModeKind
    value: NonEmptyStrictStr


def _transport_properties(properties: Mapping[object, object]) -> Mapping[str, DmJsonScalar]:
    """Validate only JSON wire shape; the injected CE codec owns DSL semantics."""

    result: dict[str, DmJsonScalar] = {}
    for raw_name, raw_value in properties.items():
        if not isinstance(raw_name, str):
            raise ValueError("DM JSON property names must be strings")
        if type(raw_value) not in {str, int, float, bool}:
            raise ValueError(f"DM JSON property {raw_name!r} must be a JSON scalar")
        result[raw_name] = _transport_scalar(raw_value)
    return MappingProxyType(result)


def _transport_scalar(value: object) -> DmJsonScalar:
    if isinstance(value, bool | str | int | float):
        return value
    raise TypeError("DM JSON property value must be a JSON scalar")


class DmJsonNodeV1(AuthoringModel):
    """One ordered descriptor node; CE's injected codec validates the registered DSL kind."""

    kind: NonEmptyStrictStr
    properties: Mapping[str, DmJsonScalar] = Field(default_factory=dict)
    content: DmJsonContentV1 | None = None
    comment: NonEmptyStrictStr | None = None
    children: tuple[DmJsonNodeV1, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def validate_transport_shape(cls, value: object) -> object:
        if not isinstance(value, Mapping):
            return value
        data = dict(value)
        raw_kind = data.get("kind")
        if isinstance(raw_kind, StrEnum):
            raw_kind = raw_kind.value
        if not isinstance(raw_kind, str):
            return data
        data["kind"] = raw_kind
        raw_properties = data.get("properties", {})
        if not isinstance(raw_properties, Mapping):
            raise ValueError("DM JSON node properties must be an object")
        data["properties"] = _transport_properties(raw_properties)
        return data

    @model_serializer(mode="wrap")
    def serialize_node(self, handler: SerializerFunctionWrapHandler) -> dict[str, object]:
        value = handler(self)
        if self.comment is None:
            value.pop("comment", None)
        return value

    @field_serializer("properties")
    def serialize_properties(self, value: Mapping[str, DmJsonScalar]) -> dict[str, DmJsonScalar]:
        return dict(value)

    @field_validator("comment")
    @classmethod
    def validate_xml_comment(cls, value: str | None) -> str | None:
        """Keep authored comments safe for deterministic XML projection."""
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("DM JSON node comment must not be blank")
        if "--" in normalized or normalized.endswith("-"):
            raise ValueError("DM JSON node comment must be valid XML comment text")
        return normalized

    @model_validator(mode="after")
    def reject_mixed_content(self) -> DmJsonNodeV1:
        if self.children and self.content is not None:
            raise ValueError(f"element {self.kind!r} cannot combine child elements and body content")
        return self


class DmJsonDocumentV1(AuthoringModel):
    """Versioned, agent-only descriptor document; it is never a workspace file."""

    version: Literal["1"] = "1"
    root: DmJsonNodeV1

    @model_validator(mode="after")
    def validate_root_node(self) -> DmJsonDocumentV1:
        if self.root.kind != EL_SETUP:
            raise ValueError("DM JSON root must be setup")
        return self

    @model_validator(mode="before")
    @classmethod
    def setup_is_the_only_root(cls, value: object) -> object:
        if not isinstance(value, Mapping):
            return value
        root = value.get("root")
        if not isinstance(root, Mapping):
            return value
        actual = root.get("kind")
        if actual == EL_SETUP:
            return value
        raise ValidationError.from_exception_data(
            cls.__name__,
            [
                {
                    "type": PydanticCustomError(
                        "authoring_enum",
                        "Input should be one of {expected}",
                        {"expected": (EL_SETUP,)},
                    ),
                    "loc": ("root", "kind"),
                    "input": actual,
                }
            ],
        )


def iter_dm_json_nodes(
    document: DmJsonDocumentV1,
) -> Iterator[tuple[DmJsonNodeV1, tuple[str | int, ...]]]:
    """Yield descriptor nodes in document order with their canonical public paths."""

    stack: list[tuple[DmJsonNodeV1, tuple[str | int, ...]]] = [(document.root, ("document", "root"))]
    while stack:
        node, path = stack.pop()
        yield node, path
        stack.extend((child, (*path, "children", index)) for index, child in reversed(tuple(enumerate(node.children))))


@dataclass(frozen=True)
class DmJsonCompilation:
    """Canonical document plus the exact XML emitted from that normalized document."""

    document: DmJsonDocumentV1
    xml: str
