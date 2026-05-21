# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Schema as the single source of truth for entity fields and types.

A :class:`FieldSpec` describes one field an entity exposes using its **real
Python type** (``str``, ``int``, ``datetime`` …). The human/JSON type string is
*derived* from that type — the type is declared once, never duplicated as a
brittle string literal.

An :class:`EntitySchema` bundles the ordered fields of one entity. Services
expose their schema's fields through ``BaseDomainService.attribute_specs`` so
the entity registry can introspect each entity by name.

Reusable groups (e.g. address) are defined here once and composed by
entities, so shared surfaces never drift.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# A field's real type: a single type, or a tuple for unions (e.g. (str, dict)).
PyType = type | tuple[type, ...]


@dataclass(frozen=True)
class FieldSpec:
    """One entity field, typed by its real Python type."""

    name: str
    py_type: PyType
    description: str
    optional: bool = False
    children: tuple[FieldSpec, ...] = ()

    @property
    def data_type(self) -> str:
        """Type string DERIVED from the real type — the type lives only once."""
        if self.children:
            base = "dict"
        elif isinstance(self.py_type, tuple):
            base = " | ".join(t.__name__ for t in self.py_type)
        else:
            base = self.py_type.__name__
        return f"{base} | None" if self.optional else base


@dataclass(frozen=True)
class EntitySchema:
    """Ordered field schema for one entity — the canonical field/type source."""

    entity: str
    fields: tuple[FieldSpec, ...]


def field(name: str, py_type: PyType, description: str, *, optional: bool = False) -> FieldSpec:
    """Build a leaf field spec."""
    return FieldSpec(name=name, py_type=py_type, description=description, optional=optional)


def group(name: str, description: str, children: Iterable[FieldSpec], *, optional: bool = False) -> FieldSpec:
    """Build a nested (dict-valued) field spec, e.g. a structured address."""
    return FieldSpec(name=name, py_type=dict, description=description, optional=optional, children=tuple(children))


# --- Shared surfaces (SPOT) -------------------------------------------------

ADDRESS_FIELDS: tuple[FieldSpec, ...] = (
    field("street", str, "Street or thoroughfare name."),
    field("house_number", str, "House or building number."),
    field("city", str, "City or locality name."),
    field("state", str, "State, province, or region."),
    field("postal_code", str, "Postal or ZIP code."),
    field("country", str, "Human-readable country name."),
    field("country_code", str, "ISO 3166-1 alpha-2 country code."),
)


def address_group(name: str = "address", description: str = "Structured postal address fields.") -> FieldSpec:
    """A reusable nested address field (shipping_address, billing_address, …)."""
    return group(name, description, ADDRESS_FIELDS)
