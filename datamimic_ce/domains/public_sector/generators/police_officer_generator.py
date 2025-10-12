from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
    from datamimic_ce.domains.common.models.demographic_config import DemographicConfig

from pathlib import Path

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_loader import (
    load_weighted_values_try_dataset,
    pick_one_weighted,
)
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class PoliceOfficerGenerator(BaseDomainGenerator):
    """Generate police officer data."""

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
    ):
        """Initialize the police officer generator.

        Args:
            dataset: The dataset to use for data generation
        """
        self._dataset = (dataset or "US").upper()  #  align dependent generators and dataset files
        self._rng: random.Random = rng or random.Random()
        from datamimic_ce.domains.common.models.demographic_config import DemographicConfig as _DC

        demo = demographic_config if demographic_config is not None else _DC()
        self._person_generator = PersonGenerator(
            dataset=self._dataset,
            demographic_config=demo,
            demographic_sampler=demographic_sampler,
            rng=self._rng,
            min_age=21,
        )
        # Hand child generators a derived RNG so seeded officers replay consistently across runs.
        self._address_generator = AddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._phone_number_generator = PhoneNumberGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._email_address_generator = EmailAddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        return self._phone_number_generator

    @property
    def email_address_generator(self) -> EmailAddressGenerator:
        return self._email_address_generator

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def rng(self) -> random.Random:
        return self._rng

    def _derive_rng(self) -> random.Random:
        # Spawn deterministic child RNGs so seeded officers replay without cross-coupling randomness.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()

    #  Centralize date generation to keep model pure and deterministic
    def generate_hire_date(self, age: int) -> str:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = __import__("datetime").datetime.now()
        # Minimum age to join: 21. Years of service cannot exceed age-21 and cap at 30
        max_years = max(0, min(30, age - 21))
        years_of_service = self._rng.randint(0, max_years)
        min_dt = (now - __import__("datetime").timedelta(days=(years_of_service + 1) * 365)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        max_dt = (now - __import__("datetime").timedelta(days=years_of_service * 365)).strftime("%Y-%m-%d %H:%M:%S")
        dt = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        import datetime as _dt

        assert isinstance(dt, _dt.datetime)
        return dt.strftime("%Y-%m-%d")

    def get_rank(self) -> str:
        """Get a random rank.

        Returns:
            A random rank.
        """
        #  use dataset_loader helpers for weighted picking
        file_path = dataset_path("public_sector", "police", f"ranks_{self._dataset}.csv", start=Path(__file__))
        loaded_weights, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        values = [row.get("rank") for row in loaded_data]
        return self._rng.choices(values, weights=loaded_weights, k=1)[0]

    def get_department(self) -> str:
        """Get a random department.

        Returns:
            A random department.
        """
        file_path = dataset_path("public_sector", "police", f"departments_{self._dataset}.csv", start=Path(__file__))
        loaded_weights, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        values = [row.get("department_id") for row in loaded_data]

        #  reduce immediate repetition while staying deterministic
        def pick() -> str:
            return self._rng.choices(values, weights=loaded_weights, k=1)[0]

        val = pick()
        last = getattr(self, "_last_department", None)
        if last == val:
            val = pick()
        self._last_department = val
        return val

    # Helper: weighted selections for officer attributes
    def pick_languages(self, *, start: Path) -> list[str]:
        values, weights = load_weighted_values_try_dataset(
            "public_sector", "police", "languages.csv", dataset=self._dataset, start=start
        )
        langs = [self._rng.choices(values, weights=weights, k=1)[0]]
        for _ in range(self._rng.randint(0, 2)):
            langs.append(self._rng.choices(values, weights=weights, k=1)[0])
        # dedupe preserve-order
        seen: set[str] = set()
        uniq: list[str] = []
        for lang in langs:
            if lang not in seen:
                seen.add(lang)
                uniq.append(lang)
        return uniq

    def pick_shift(self, *, start: Path) -> str:
        values, weights = load_weighted_values_try_dataset(
            "public_sector", "police", "shifts.csv", dataset=self._dataset, start=start
        )
        return pick_one_weighted(self._rng, values, weights)

    def pick_certifications(self, *, start: Path) -> list[str]:
        values, weights = load_weighted_values_try_dataset(
            "public_sector", "police", "certifications.csv", dataset=self._dataset, start=start
        )
        k = self._rng.randint(1, min(4, len(values)))
        if k >= len(values):
            return list(values)
        return self._rng.sample(list(values), k)

    # Helper: pick unit; prefer dataset if available, otherwise use a small static set (WHY: until dataset is added)
    def pick_unit(self) -> str:
        #  Reuse departments dataset until a dedicated units dataset exists
        file_path = dataset_path("public_sector", "police", f"departments_{self._dataset}.csv", start=Path(__file__))
        loaded_weights, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        values = [row.get("department_id") for row in loaded_data]
        val = self._rng.choices(values, weights=loaded_weights, k=1)[0]
        last = getattr(self, "_last_unit", None)
        if last == val and len(values) > 1:
            val = self._rng.choices(values, weights=loaded_weights, k=1)[0]
        self._last_unit = val
        return val
