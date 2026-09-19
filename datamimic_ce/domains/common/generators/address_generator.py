# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random
from dataclasses import dataclass

from datamimic_ce.domains.common.generators.city_generator import CityGenerator
from datamimic_ce.domains.common.generators.country_generator import CountryGenerator
from datamimic_ce.domains.common.generators.region_groups import REGION_GROUPS
from datamimic_ce.domains.common.literal_generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.literal_generators.street_name_generator import StreetNameGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import DatasetAwareDomainGenerator


@dataclass(frozen=True)
class AddressRow:
    """The concrete country and sub-generators resolved for ONE address (one row)."""

    dataset: str
    city_generator: CityGenerator
    country_generator: CountryGenerator
    phone_number_generator: PhoneNumberGenerator
    street_name_generator: StreetNameGenerator


class AddressGenerator(DatasetAwareDomainGenerator):
    """Generator for address data.

    This class generates random address data using the data from datasets.

    ``dataset`` may also be a region-group alias (e.g. ``"europe"``, see
    :data:`REGION_GROUPS`) - each row (see :meth:`resolve_row`) then independently draws a
    concrete country from the group, since a single ``AddressGenerator`` instance is reused
    across every row of a run (resolving the country once here in ``__init__`` would give
    every row in the run the same one, not variety).
    """

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        """Initialize the AddressGenerator.

        Args:
            dataset: The dataset to use for generating addresses, or a region-group alias.
            rng: Optional seeded random instance for deterministic output.
        """
        super().__init__(dataset=dataset, rng=rng)
        self._company_name_generator = CompanyNameGenerator(rng=self._derive_rng())

        self._region_codes = REGION_GROUPS.get(self._dataset)
        self._row_cache: dict[str, AddressRow] = {}
        if self._region_codes is None:
            # Single concrete dataset (the common case): build once, same as before this class
            # supported region groups - identical behavior, zero per-row overhead.
            self._row_cache[self._dataset] = self._build_row(self._dataset)

    def _build_row(self, dataset: str) -> AddressRow:
        return AddressRow(
            dataset=dataset,
            city_generator=CityGenerator(dataset=dataset, rng=self._derive_rng()),
            country_generator=CountryGenerator(dataset=dataset, rng=self._derive_rng()),
            phone_number_generator=PhoneNumberGenerator(dataset=dataset, rng=self._derive_rng()),
            street_name_generator=StreetNameGenerator(dataset=dataset, rng=self._derive_rng()),
        )

    def resolve_row(self) -> AddressRow:
        """The concrete dataset and sub-generators for ONE address. A single concrete dataset
        always resolves to the same (cached) row. A region group draws a fresh country each call,
        reusing a previously-built row for a country drawn again."""
        dataset = self._rng.choice(self._region_codes) if self._region_codes is not None else self._dataset
        if dataset not in self._row_cache:
            self._row_cache[dataset] = self._build_row(dataset)
        return self._row_cache[dataset]

    @property
    def company_name_generator(self) -> CompanyNameGenerator:
        """Get the company name generator.

        Returns:
            The company name generator.
        """
        return self._company_name_generator
