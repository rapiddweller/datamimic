"""Pure demographic sampler built on top of demographic profiles."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from random import Random

from .profile import (
    DemographicAgeBand,
    DemographicConditionRate,
    DemographicProfile,
    DemographicProfileId,
    SexKey,
    normalize_sex,
)


@dataclass(frozen=True)
class DemographicSample:
    """Sampled demographic attributes for a single entity."""

    age: int | None
    sex: SexKey
    conditions: frozenset[str]


class DemographicSampler:
    """Pure sampler that draws ages, sexes and conditions from a profile."""

    def __init__(self, profile: DemographicProfile):
        self._profile = profile
        self._age_cdf = self._build_age_cdfs(profile)
        self._sex_choices = self._build_sex_choices(profile)

    @property
    def profile_id(self) -> DemographicProfileId:
        return self._profile.profile_id

    def sample_age_sex(self, rng: Random) -> tuple[int, SexKey]:
        """Sample an age band and sex using cumulative weights."""

        sex = self._choose_sex(rng)
        bands = self._age_cdf.get(sex) or self._age_cdf.get(None)
        if not bands:
            raise ValueError("No age bands available for demographic sampling")
        pick = rng.random()
        for threshold, band in bands:
            if pick <= threshold:
                age = rng.randint(band.age_min, band.age_max)
                return age, sex
        # Numerical precision might leave pick slightly above the last threshold.
        last_band = bands[-1][1]
        # Guarantee a return even when float rounding pushes us past the final threshold.
        return rng.randint(last_band.age_min, last_band.age_max), sex

    def sample_conditions(self, age: int, sex: SexKey, rng: Random) -> frozenset[str]:
        """Sample independent conditions based on prevalence tables."""

        selected: set[str] = set()
        normalized_sex = normalize_sex(sex)
        for condition, rates in self._profile.condition_rates.items():
            rate = self._select_rate(rates, age, normalized_sex)
            if rate is None:
                continue
            if rng.random() <= rate.prevalence:
                selected.add(condition)
        return frozenset(selected)

    def _select_rate(
        self,
        rates: Iterable[DemographicConditionRate],
        age: int,
        sex: SexKey,
    ) -> DemographicConditionRate | None:
        # Prefer exact sex match, otherwise fall back to combined entries.
        exact_match = None
        fallback = None
        for rate in rates:
            if not rate.matches(age=age, sex=sex):
                continue
            if rate.sex is None:
                fallback = rate
            else:
                exact_match = rate
                break
        return exact_match or fallback

    def _build_age_cdfs(self, profile: DemographicProfile) -> dict[SexKey, list[tuple[float, DemographicAgeBand]]]:
        cdfs: dict[SexKey, list[tuple[float, DemographicAgeBand]]] = {}
        for sex, bands in profile.age_bands.items():
            cumulative = 0.0
            cdf: list[tuple[float, DemographicAgeBand]] = []
            for band in bands:
                cumulative += band.weight
                cdf.append((cumulative, band))
            if not cdf:
                continue
            # Normalize trailing rounding differences so cumulative ends at 1.0.
            final_threshold, last_band = cdf[-1]
            if abs(final_threshold - 1.0) > 1e-9:
                adjust = final_threshold
                cdf = [(threshold / adjust, band) for threshold, band in cdf]
            cdfs[sex] = cdf
        return cdfs

    def _build_sex_choices(self, profile: DemographicProfile) -> tuple[SexKey, ...]:
        # Use deterministic ordering so seeded RNGs replay the same sex sequence across runs.
        sexes = sorted(sex for sex in profile.sexes() if sex is not None)
        if not sexes:
            return (None,)
        return tuple(sexes)

    def _choose_sex(self, rng: Random) -> SexKey:
        if not self._sex_choices:
            return None
        # Treat provided sex buckets as equally likely until we collect richer priors (future roadmap).
        return rng.choice(self._sex_choices)
