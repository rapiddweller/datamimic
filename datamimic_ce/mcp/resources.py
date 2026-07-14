"""Expose JSON Schema resources for MCP clients."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import JsonValue, TypeAdapter, ValidationError

from datamimic_ce.domains import facade


class SchemaKind(StrEnum):
    """Closed schema-resource variants; values remain wire-compatible strings."""

    REQUEST = "request"
    RESPONSE = "response"


SchemaDocument = dict[str, JsonValue]
_SCHEMA_DOCUMENT_ADAPTER = TypeAdapter(SchemaDocument)


@dataclass(frozen=True)
class SchemaResource:
    """Descriptor for a domain schema resource."""

    domain: str
    version: str
    kind: SchemaKind

    @property
    def uri(self) -> str:
        """Return the canonical MCP resource URI."""
        return f"resource://datamimic/schemas/{self.domain}/{self.version}/{self.kind}.json"

    @property
    def path(self) -> Path:
        """Resolve the on-disk schema path for the resource."""
        filename = f"{self.domain}.{self.version}.{self.kind}.json"
        return Path(__file__).resolve().parents[1] / "domains" / "schemas" / filename


def iter_schema_resources() -> Iterator[SchemaResource]:
    """Yield schema descriptors for each domain and version pair."""
    for domain, version in sorted(facade.REGISTRY):
        yield SchemaResource(domain=domain, version=version, kind=SchemaKind.REQUEST)
        yield SchemaResource(domain=domain, version=version, kind=SchemaKind.RESPONSE)


def _validate_schema_document(data: object, path: Path) -> SchemaDocument:
    try:
        return _SCHEMA_DOCUMENT_ADAPTER.validate_python(data, strict=True)
    except ValidationError as err:
        raise TypeError(f"Schema at {path} must decode into a JSON object") from err


def load_schema(domain: str, version: str, kind: SchemaKind) -> SchemaDocument:
    """Load a schema document from disk using the canonical registry layout."""
    resource = SchemaResource(domain=domain, version=version, kind=kind)
    path = resource.path
    if not path.exists():
        raise FileNotFoundError(f"Missing schema file for {resource.uri}")
    with path.open("r", encoding="utf-8") as handle:
        data: object = json.load(handle)
    return _validate_schema_document(data, path)


__all__ = [
    "SchemaDocument",
    "SchemaKind",
    "SchemaResource",
    "iter_schema_resources",
    "load_schema",
]
