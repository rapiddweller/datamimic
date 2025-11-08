"""Expose JSON Schema resources for MCP clients."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from datamimic_ce.domains import facade

SchemaKind = Literal["request", "response"]


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
        yield SchemaResource(domain=domain, version=version, kind="request")
        yield SchemaResource(domain=domain, version=version, kind="response")


def load_schema(domain: str, version: str, kind: SchemaKind) -> dict[str, Any]:
    """Load a schema document from disk using the canonical registry layout."""
    resource = SchemaResource(domain=domain, version=version, kind=kind)
    path = resource.path
    if not path.exists():
        raise FileNotFoundError(f"Missing schema file for {resource.uri}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):  # Defensive guardrail for schema drift.
        raise TypeError(f"Schema at {path} must decode into an object")
    return cast(dict[str, Any], data)


__all__ = ["SchemaResource", "SchemaKind", "iter_schema_resources", "load_schema"]
