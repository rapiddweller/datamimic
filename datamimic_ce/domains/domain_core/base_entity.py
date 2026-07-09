# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from abc import ABC, abstractmethod
from typing import Any

from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator


class BaseEntity(ABC):
    """
    Base class for all domain entities.

    This class provides common functionality for all entity objects used in domain models,
    including property access and validation.
    """

    def __init__(self, generator: BaseDomainGenerator | None = None):
        # Cache for generated values
        self._field_cache: dict[str, Any] = {}
        # self._generator = generator

    @property
    def field_cache(self):
        return self._field_cache

    @classmethod
    def _canonical_fields(cls) -> dict[str, str]:
        """Map each public field, normalized (lowercased, separators removed), to its real name. Cached per
        class. Lets ``givenName``/``given_name``/``GIVEN_NAME`` all resolve to the canonical ``given_name``."""
        cache = cls.__dict__.get("_canonical_fields_cache")
        if cache is None:
            cache = {a.replace("_", "").lower(): a for a in dir(cls) if not a.startswith("_")}
            cls._canonical_fields_cache = cache  # type: ignore[attr-defined]
        return cache

    def __getattr__(self, name: str) -> Any:
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

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary."""
        raise NotImplementedError("Subclasses must implement this method.")


def stringify_if_entity(value: Any) -> Any:
    """A whole entity bound into a scalar column (e.g. `<key script="person">` into a varchar/
    string field, the legacy toString() idiom) has no sane driver-level representation - both the
    RDBMS and Mongo write paths call this first. `BaseEntity` defines no `__str__`, so a bare
    `str(value)` would write Python's default `<...Person object at 0x...>` (a non-deterministic
    memory address); `.to_dict()` is the one meaningful representation every entity provides."""
    return str(value.to_dict()) if isinstance(value, BaseEntity) else value
