# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterator
from functools import cache
from typing import TYPE_CHECKING

from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.engine.dsl.contracts import EntityValue

if TYPE_CHECKING:
    from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec


class BaseEntity(EntityValue):
    """
    Base class for all domain entities.

    This class provides common functionality for all entity objects used in domain models,
    including property access and validation.
    """

    def __init__(self, generator: BaseDomainGenerator | None = None):
        # Cache for generated values
        self._field_cache: dict[str, object] = {}
        self._identifier_registry: dict[tuple[str, str], set[str]] | None = None
        self._entity_name = type(self).__name__
        self._unique_identifier_formats: dict[str, str] = {}
        self._nested_identifier_schemas: dict[str, EntitySchema] = {}
        # self._generator = generator

    @property
    def field_cache(self) -> dict[str, object]:
        return self._field_cache

    @classmethod
    @cache
    def _canonical_fields(cls) -> dict[str, str]:
        """Map each public field, normalized (lowercased, separators removed), to its real name. Cached per
        class. Lets ``givenName``/``given_name``/``GIVEN_NAME`` all resolve to the canonical ``given_name``."""
        return {a.replace("_", "").lower(): a for a in dir(cls) if not a.startswith("_")}

    def __getattr__(self, name: str) -> object:
        # Only runs when normal lookup misses: resolve a non-canonical field name (e.g. a legacy descriptor's camelCase
        # ``person.givenName``) to the entity's real snake_case field. Zero cost on the canonical path.
        if name.startswith("_"):
            raise AttributeError(name)
        fields = type(self)._canonical_fields()
        real = fields.get(name.replace("_", "").lower())
        if real is not None and real != name:
            return getattr(self, real)
        avail = sorted(fields.values())
        raise AttributeError(f"'{type(self).__name__}' entity has no field '{name}'. Available: {avail}")

    def _bind_identifier_registry(
        self,
        registry: dict[tuple[str, str], set[str]],
        entity_name: str,
        attributes: tuple[FieldSpec, ...],
        nested_schemas: dict[str, EntitySchema],
    ) -> None:
        self._identifier_registry = registry
        self._entity_name = entity_name
        self._nested_identifier_schemas = nested_schemas
        self._unique_identifier_formats = {
            field.name: field.unique_identifier_format
            for field in attributes
            if field.unique_identifier_format is not None
        }

    def _claim_identifier(self, name: str, candidate: str) -> str:
        identifier_format = self._unique_identifier_formats.get(name)
        registry = self._identifier_registry
        if identifier_format is None or registry is None:
            return candidate

        key = (self._entity_name, name)
        if key not in registry:
            registry[key] = set()
        seen = registry[key]
        if candidate not in seen:
            registry[key] = seen | {candidate}
            return candidate

        for alternative in _identifier_alternatives(identifier_format, candidate, len(seen)):
            if alternative not in seen:
                registry[key] = seen | {alternative}
                return alternative

        raise ValueError(f"Unique identifier space exhausted for {self._entity_name}.{name}")

    def _bind_nested_identifier(self, name: str, entity: BaseEntity) -> None:
        schema = self._nested_identifier_schemas.get(name)
        if self._identifier_registry is not None and schema is not None:
            entity._bind_identifier_registry(self._identifier_registry, schema.entity, schema.fields, {})

    @abstractmethod
    def to_dict(self) -> dict[str, object]:
        """Convert the entity to a dictionary."""
        raise NotImplementedError("Subclasses must implement this method.")


def _identifier_alternatives(identifier_format: str, candidate: str, seen_count: int) -> Iterator[str]:
    if identifier_format == "uuid4":
        import uuid

        fixed_mask = (0xF << 76) | (0b11 << 62)
        bit_positions = tuple(bit for bit in range(128) if not (fixed_mask >> bit) & 1)
        capacity = 1 << len(bit_positions)
        if seen_count >= capacity:
            return
        try:
            value = uuid.UUID(candidate)
        except ValueError as error:
            raise ValueError(f"Unique identifier {candidate!r} does not match uuid4 format") from error
        if value.version != 4 or value.variant != uuid.RFC_4122:
            raise ValueError(f"Unique identifier {candidate!r} does not match uuid4 format")
        rank = sum(((value.int >> bit) & 1) << index for index, bit in enumerate(bit_positions))
        for offset in range(1, capacity + 1):
            next_rank = (rank + offset) % capacity
            next_value = 0x4 << 76 | 0b10 << 62
            for index, bit in enumerate(bit_positions):
                next_value |= ((next_rank >> index) & 1) << bit
            yield str(uuid.UUID(int=next_value))
        return

    import re

    match = re.fullmatch(r"([^[]*)\[([^]]+)\]\{(\d+)\}", identifier_format)
    if match is None:
        raise ValueError(f"Unsupported unique identifier format: {identifier_format!r}")
    prefix, charset, raw_length = match[1], match[2], match[3]
    alphabet: list[str] = []
    index = 0
    while index < len(charset):
        if index + 2 < len(charset) and charset[index + 1] == "-":
            alphabet.extend(chr(code) for code in range(ord(charset[index]), ord(charset[index + 2]) + 1))
            index += 3
        else:
            alphabet.append(charset[index])
            index += 1
    length = int(raw_length)
    capacity = len(alphabet) ** length
    if seen_count >= capacity:
        return
    if not candidate.startswith(prefix) or len(candidate) != len(prefix) + length:
        raise ValueError(f"Unique identifier {candidate!r} does not match {identifier_format!r}")
    suffix = candidate[len(prefix) :]
    try:
        rank = 0
        for character in suffix:
            rank = rank * len(alphabet) + alphabet.index(character)
    except ValueError as error:
        raise ValueError(f"Unique identifier {candidate!r} does not match {identifier_format!r}") from error
    for offset in range(1, capacity + 1):
        next_rank = (rank + offset) % capacity
        digits = [alphabet[0]] * length
        for position in range(length - 1, -1, -1):
            next_rank, digit = divmod(next_rank, len(alphabet))
            digits[position] = alphabet[digit]
        yield prefix + "".join(digits)
