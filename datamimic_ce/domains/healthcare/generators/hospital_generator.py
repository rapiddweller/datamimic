# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Hospital generator utilities.

This module provides utility functions for generating hospital data.
"""

import random
from pathlib import Path

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator


class HospitalGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None, rng: random.Random | None = None) -> None:
        #  normalize dataset to ISO upper-case to map to suffixed CSVs consistently
        self._dataset = (dataset or "US").upper()
        self._rng: random.Random = rng or random.Random()
        self._address_generator = AddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._phone_number_generator = PhoneNumberGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._last_type: str | None = None

    @property
    def dataset(self) -> str:
        """Get the dataset.

        Returns:
            The dataset.
        """
        return self._dataset

    @property
    def address_generator(self) -> AddressGenerator:
        """Get the address generator.

        Returns:
            The address generator.
        """
        return self._address_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        """Get the phone number generator.

        Returns:
            The phone number generator.
        """
        return self._phone_number_generator

    @property
    def rng(self) -> random.Random:
        return self._rng

    def _derive_rng(self) -> random.Random:
        # Spawn child RNGs so seeded hospitals can replay deterministically without coupling downstream draws.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()

    def generate_hospital_name(self, city: str, state: str) -> str:
        """Generate a hospital name based on location.

        Args:
            city: The city where the hospital is located.
            state: The state where the hospital is located.

        Returns:
            A hospital name.
        """
        # Load name patterns from dataset
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        patterns, w = load_weighted_values_try_dataset(
            "healthcare", "hospital", "name_patterns.csv", dataset=self._dataset, start=Path(__file__)
        )
        pattern = self._rng.choices(patterns, weights=w, k=1)[0]

        # Fill in the pattern with the city and state
        return pattern.format(city=city, state=state)

    def get_hospital_type(self):
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        values, w = load_weighted_values_try_dataset(
            "healthcare", "hospital", "hospital_types.csv", dataset=self._dataset, start=Path(__file__)
        )
        # avoid immediate repetition when possible
        if self._last_type in values and len(values) > 1:
            pool = [(v, float(wi)) for v, wi in zip(values, w, strict=False) if v != self._last_type]
            p_vals, p_w = zip(*pool, strict=False)
            choice = self._rng.choices(list(p_vals), weights=list(p_w), k=1)[0]
        else:
            choice = self._rng.choices(values, weights=w, k=1)[0]
        self._last_type = choice
        return choice

    def generate_departments(self, hospital_type: str, count: int | None = None) -> list[str]:
        """Generate a list of hospital departments.

        Returns:
            A list of hospital departments.
        """

        # Define common departments for all hospital types

        # Define specialty departments by hospital type

        # Switch to dataset-driven departments
        slug = hospital_type.lower().replace(" ", "_").replace("'", "")
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        try:
            values, w = load_weighted_values_try_dataset(
                "healthcare", "hospital", f"departments_{slug}.csv", dataset=self._dataset, start=Path(__file__)
            )
        except FileNotFoundError:
            #  If no specific department list for the type exists, fall back to 'general'
            values, w = load_weighted_values_try_dataset(
                "healthcare", "hospital", "departments_general.csv", dataset=self._dataset, start=Path(__file__)
            )
        if count is None:
            if hospital_type == "Specialty":
                count = self._rng.randint(5, 10)
            elif hospital_type == "Community":
                count = self._rng.randint(8, 15)
            else:
                count = self._rng.randint(10, 20)
        if count >= len(values):
            return sorted(values)
        pool = list(values)
        pool_w = [float(x) for x in w]
        selected: list[str] = []
        for _ in range(count):
            chosen = self._rng.choices(pool, weights=pool_w, k=1)[0]
            selected.append(chosen)
            idx = pool.index(chosen)
            del pool[idx]
            del pool_w[idx]
        return sorted(selected)

    def generate_services(self, hospital_type: str, departments: list[str], count: int | None = None) -> list[str]:
        """Generate a list of hospital services from datasets (no hardcoded fallbacks)."""
        slug = hospital_type.lower().replace(" ", "_").replace("'", "")
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        try:
            values, w = load_weighted_values_try_dataset(
                "healthcare", "hospital", f"services_{slug}.csv", dataset=self._dataset, start=Path(__file__)
            )
        except FileNotFoundError:
            #  If no specific services list for the type exists, fall back to 'general'
            values, w = load_weighted_values_try_dataset(
                "healthcare", "hospital", "services_general.csv", dataset=self._dataset, start=Path(__file__)
            )
        if count is None:
            if hospital_type == "Specialty":
                count = self._rng.randint(10, 20)
            elif hospital_type == "Community":
                count = self._rng.randint(15, 25)
            else:
                count = self._rng.randint(20, 40)
        if count >= len(values):
            return sorted(values)
        pool = list(values)
        pool_w = [float(x) for x in w]
        selected: list[str] = []
        for _ in range(count):
            chosen = self._rng.choices(pool, weights=pool_w, k=1)[0]
            selected.append(chosen)
            idx = pool.index(chosen)
            del pool[idx]
            del pool_w[idx]
        return sorted(selected)

    def generate_accreditation(self, hospital_type: str) -> list[str]:
        """Generate a list of hospital accreditations from datasets."""
        slug = hospital_type.lower().replace(" ", "_").replace("'", "")
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        try:
            values, w = load_weighted_values_try_dataset(
                "healthcare", "hospital", f"accreditations_{slug}.csv", dataset=self._dataset, start=Path(__file__)
            )
        except FileNotFoundError:
            #  If no specific accreditations for the type exist, fall back to 'general'
            values, w = load_weighted_values_try_dataset(
                "healthcare", "hospital", "accreditations_general.csv", dataset=self._dataset, start=Path(__file__)
            )
        # Determine how many accreditations to include
        if hospital_type == "Specialty":
            k = self._rng.randint(2, 4)
        elif hospital_type == "Community":
            k = self._rng.randint(1, 3)
        else:
            k = self._rng.randint(3, 5)
        if k >= len(values):
            return sorted(values)
        pool = list(values)
        pool_w = [float(x) for x in w]
        selected: list[str] = []
        for _ in range(k):
            chosen = self._rng.choices(pool, weights=pool_w, k=1)[0]
            selected.append(chosen)
            idx = pool.index(chosen)
            del pool[idx]
            del pool_w[idx]
        return sorted(selected)
