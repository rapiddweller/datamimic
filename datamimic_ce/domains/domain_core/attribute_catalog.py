# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Attribute metadata for domain entities.

An :class:`AttributeSpec` describes one field a domain entity exposes (the
columns a DSL ``<generate>`` can read via ``entity.<attr>``). Services declare
their attributes through ``BaseDomainService.attribute_specs`` so the entity
registry can introspect and document each entity by name.

Reusable group specs (address, contact) live here as the single source of
truth — multiple entities share those surfaces and must not drift.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class AttributeSpec:
    """Immutable description of an entity attribute."""

    name: str
    data_type: str
    description: str
    children: tuple[AttributeSpec, ...] = ()


def specs(*pairs: tuple[str, str, str]) -> tuple[AttributeSpec, ...]:
    """Build a tuple of leaf specs from ``(name, type, description)`` triples.

    Keeps per-service declarations terse and uniform.
    """
    return tuple(AttributeSpec(name, data_type, description) for name, data_type, description in pairs)


def group(name: str, description: str, children: Iterable[AttributeSpec]) -> AttributeSpec:
    """Build a nested (dict-valued) attribute spec, e.g. a structured address."""
    return AttributeSpec(name, "dict", description, tuple(children))


def spec_to_dict(spec: AttributeSpec) -> dict[str, object]:
    """Render an AttributeSpec (recursively) into a JSON-serialisable dict."""
    payload: dict[str, object] = {
        "name": spec.name,
        "type": spec.data_type,
        "description": spec.description,
    }
    if spec.children:
        payload["children"] = [spec_to_dict(child) for child in spec.children]
    return payload


# --- Shared surfaces (SPOT) -------------------------------------------------

ADDRESS_SPECS: tuple[AttributeSpec, ...] = specs(
    ("street", "str", "Street or thoroughfare name."),
    ("house_number", "str", "House or building number."),
    ("city", "str", "City or locality name."),
    ("state", "str", "State, province, or region."),
    ("postal_code", "str", "Postal or ZIP code."),
    ("country", "str", "Human-readable country name."),
    ("country_code", "str", "ISO 3166-1 alpha-2 country code."),
)

ADDRESS_GROUP_SPEC = group("address", "Structured postal address fields.", ADDRESS_SPECS)

CONTACT_SPECS: tuple[AttributeSpec, ...] = specs(
    ("phone", "str", "Contact phone number."),
    ("mobile_phone", "str", "Mobile contact number."),
    ("email", "str", "Primary email address."),
)
