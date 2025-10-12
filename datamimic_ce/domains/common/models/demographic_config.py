"""Demographic configuration utilities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class DemographicConfig:
    """Container for demographic overrides used across generators."""

    age_min: int | None = None
    age_max: int | None = None
    conditions_include: frozenset[str] | None = None
    conditions_exclude: frozenset[str] | None = None
    transaction_profile: str | Mapping[str, float] | None = None

    def with_defaults(
        self,
        *,
        default_age_min: int | None = None,
        default_age_max: int | None = None,
    ) -> DemographicConfig:
        """Return a copy where missing bounds fall back to defaults."""

        return DemographicConfig(
            age_min=self.age_min if self.age_min is not None else default_age_min,
            age_max=self.age_max if self.age_max is not None else default_age_max,
            conditions_include=self.conditions_include,
            conditions_exclude=self.conditions_exclude,
            transaction_profile=self.transaction_profile,
        )

    def normalized_includes(self) -> frozenset[str]:
        """Return include set with a deterministic container."""

        return frozenset(self.conditions_include or ())

    def normalized_excludes(self) -> frozenset[str]:
        """Return exclude set with a deterministic container."""

        return frozenset(self.conditions_exclude or ())
