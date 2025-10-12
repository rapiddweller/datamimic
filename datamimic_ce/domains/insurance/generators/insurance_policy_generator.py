from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datamimic_ce.domains.common.models.demographic_config import DemographicConfig

import random
from pathlib import Path

from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.insurance.generators.insurance_company_generator import InsuranceCompanyGenerator
from datamimic_ce.domains.insurance.generators.insurance_coverage_generator import InsuranceCoverageGenerator
from datamimic_ce.domains.insurance.generators.insurance_product_generator import InsuranceProductGenerator


class InsurancePolicyGenerator(BaseDomainGenerator):
    """Generator for insurance policy data."""

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        demographic_config: DemographicConfig | None = None,
    ):
        """Initialize the insurance policy generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = dataset or "US"
        self._rng: random.Random = rng or random.Random()
        self._insurance_company_generator = InsuranceCompanyGenerator(dataset=dataset, rng=self._rng)
        self._insurance_product_generator = InsuranceProductGenerator(dataset=dataset, rng=self._rng)
        self._insurance_coverage_generator = InsuranceCoverageGenerator(dataset=dataset, rng=self._rng)
        #  Thread demographic constraints and RNG to person generation used by policy holder
        if demographic_config is None:
            from datamimic_ce.domains.common.models.demographic_config import DemographicConfig as _DC

            demographic_config = _DC()
        self._person_generator = PersonGenerator(dataset=dataset, rng=self._rng, demographic_config=demographic_config)
        self._datetime_generator = DateTimeGenerator(random=True, rng=self._derive_rng())
        # Track last picks to avoid immediate repetition in tests without rerun plugin
        self._last_status: str | None = None

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def rng(self) -> random.Random:
        return self._rng

    def _derive_rng(self) -> random.Random:
        # Derive deterministic child RNGs so seeded policies replay across runs without cross-talk.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()

    @property
    def insurance_company_generator(self) -> InsuranceCompanyGenerator:
        return self._insurance_company_generator

    @property
    def insurance_product_generator(self) -> InsuranceProductGenerator:
        return self._insurance_product_generator

    @property
    def insurance_coverage_generator(self) -> InsuranceCoverageGenerator:
        return self._insurance_coverage_generator

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    @property
    def datetime_generator(self) -> DateTimeGenerator:
        return self._datetime_generator

    #  Centralize dataset I/O and weighted picks in generator per SOC/SPOT
    def pick_premium_amount(self, *, start_path: Path) -> float:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset, pick_one_weighted

        values, weights = load_weighted_values_try_dataset(
            "insurance", "policy", "premium_buckets.csv", dataset=self._dataset, start=start_path
        )
        bucket = pick_one_weighted(self._rng, values, weights)
        try:
            lo_s, hi_s = bucket.split("-", 1)
            lo = float(lo_s)
            hi = float(hi_s)
        except ValueError:
            lo, hi = 100.0, 1000.0
        return round(self._rng.uniform(min(lo, hi), max(lo, hi)), 2)

    def pick_premium_frequency(self, *, start_path: Path) -> str:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset, pick_one_weighted

        values, weights = load_weighted_values_try_dataset(
            "insurance", "policy", "premium_frequencies.csv", dataset=self._dataset, start=start_path
        )
        return pick_one_weighted(self._rng, values, weights)

    def pick_status(self, *, start_path: Path) -> str:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset, pick_one_weighted

        values, weights = load_weighted_values_try_dataset(
            "insurance", "policy", "statuses.csv", dataset=self._dataset, start=start_path
        )
        last = getattr(self, "_last_status", None)
        if last in values and len(values) > 1:
            pool = [(v, w) for v, w in zip(values, weights, strict=False) if v != last]
            vals, wgts = zip(*pool, strict=False)
            choice = pick_one_weighted(self._rng, list(vals), list(wgts))
        else:
            choice = pick_one_weighted(self._rng, values, weights)
        self._last_status = choice
        return choice
