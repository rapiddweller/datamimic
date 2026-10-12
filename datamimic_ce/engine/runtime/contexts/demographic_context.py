"""Context wiring for demographic samplers."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from datamimic_ce.domains.api import DemographicConfig, DemographicProfileId, DemographicSampler


@dataclass(frozen=True)
class DemographicContext:
    """Immutable container for the active demographic profile."""

    profile_id: DemographicProfileId
    sampler: DemographicSampler
    overrides: DemographicConfig | None
    rng: Random
