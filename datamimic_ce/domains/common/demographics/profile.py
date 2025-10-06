"""Demographic profile domain objects."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

SexKey = str | None


def normalize_sex(sex: str | None) -> SexKey:
    """Normalize raw sex codes coming from CSV files."""

    if sex is None:
        return None
    value = sex.strip().upper()
    return value or None


@dataclass(frozen=True)
class DemographicProfileId:
    """Stable identifier for a demographic profile dataset."""

    dataset: str
    version: str


@dataclass(frozen=True)
class DemographicAgeBand:
    """Age distribution entry scoped to a sex bucket."""

    sex: SexKey
    age_min: int
    age_max: int
    weight: float

    def contains(self, age: int) -> bool:
        return self.age_min <= age <= self.age_max


@dataclass(frozen=True)
class DemographicConditionRate:
    """Condition prevalence entry used for Bernoulli sampling."""

    condition: str
    sex: SexKey
    age_min: int
    age_max: int
    prevalence: float

    def matches(self, *, age: int, sex: SexKey) -> bool:
        return self.age_min <= age <= self.age_max and (self.sex is None or self.sex == sex)


@dataclass(frozen=True)
class DemographicProfile:
    """Collection of demographic priors used by samplers."""

    profile_id: DemographicProfileId
    age_bands: Mapping[SexKey, tuple[DemographicAgeBand, ...]]
    condition_rates: Mapping[str, tuple[DemographicConditionRate, ...]]

    def bands_for_sex(self, sex: SexKey) -> tuple[DemographicAgeBand, ...]:
        """Return ordered bands for a given sex, falling back to combined data."""

        normalized = normalize_sex(sex)
        if normalized in self.age_bands:
            return self.age_bands[normalized]
        # Combined (sex-less) priors should backstop missing sex specific data without failing generation.
        return self.age_bands.get(None, ())

    def conditions_for(self, condition: str) -> tuple[DemographicConditionRate, ...]:
        """Return ordered prevalence rows for a condition."""

        return self.condition_rates.get(condition, ())

    def sexes(self) -> Sequence[SexKey]:
        """Expose the known sex buckets for downstream logic."""

        return tuple(self.age_bands.keys())
