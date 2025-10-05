# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office generator utilities.

This module provides utility functions for generating administration office data.
"""

import random
from pathlib import Path
from typing import TypeVar

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.domains.common.literal_generators.given_name_generator import GivenNameGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_loader import (
    load_weighted_values_try_dataset,
    pick_one_weighted,
)
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil

T = TypeVar("T")  # Define a type variable for generic typing


class AdministrationOfficeGenerator(BaseDomainGenerator):
    """Generator for administration office data."""

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        """Initialize the administration office generator.

        Args:
            dataset: The country code to use for data generation
        """
        self._dataset = (dataset or "US").upper()  #  propagate normalized dataset to dependent generators
        self._rng = rng or random.Random()  #  deterministic RNG injection point
        # Derive child RNGs so seeded administration offices replay deterministic nested attributes.
        self._address_generator = AddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._phone_number_generator = PhoneNumberGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._family_name_generator = FamilyNameGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._given_name_generator = GivenNameGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        # Track last office type to avoid immediate repetition in successive generations
        self._last_office_type: str | None = None
        # Track last jurisdiction to reduce immediate repetition across entities
        self._last_jurisdiction: str | None = None
        # Track last hours signature to reduce repetition across entities
        self._last_hours_signature: tuple[tuple[str, str], ...] | None = None
        # Track last staff count to reduce identical consecutive draws
        self._last_staff_count: int | None = None

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        return self._phone_number_generator

    @property
    def family_name_generator(self) -> FamilyNameGenerator:
        return self._family_name_generator

    @property
    def given_name_generator(self) -> GivenNameGenerator:
        return self._given_name_generator

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def rng(self) -> random.Random:
        return self._rng

    def _derive_rng(self) -> random.Random:
        # Spawn deterministic child RNGs so seeded offices replay consistently without sharing streams.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()

    # Helper: pick office type from dataset using weighted values with anti-repeat
    def pick_office_type(self) -> str:
        values, weights = load_weighted_values_try_dataset(
            "public_sector",
            "administration",
            "office_types.csv",
            dataset=self._dataset,
            start=Path(__file__),
        )
        choice = pick_one_weighted(self._rng, values, weights)
        # simple anti-repeat: redraw once if same and >1 options
        if self._last_office_type == choice and len(values) > 1:
            choice = pick_one_weighted(self._rng, values, weights)
        self._last_office_type = choice
        return choice

    # Helper: pick jurisdiction bucket from dataset (city/county/state/federal)
    def pick_jurisdiction_bucket(self) -> str:
        values, weights = load_weighted_values_try_dataset(
            "public_sector",
            "administration",
            "jurisdictions.csv",
            dataset=self._dataset,
            start=Path(__file__),
        )
        pick = pick_one_weighted(self._rng, values, weights).lower()
        # minimal anti-repeat redraw
        if self._last_jurisdiction and pick == str(self._last_jurisdiction).lower() and len(values) > 1:
            pick = pick_one_weighted(self._rng, values, weights).lower()
        self._last_jurisdiction = pick
        return pick

    # Helper: build office name using dataset patterns (US fallback handled by dataset_path)
    def build_office_name(self, city: str, state: str, office_type: str, jurisdiction: str) -> str:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        patterns, w = load_weighted_values_try_dataset(
            "public_sector", "administration", "name_patterns.csv", dataset=self._dataset, start=Path(__file__)
        )
        pattern = self._rng.choices(patterns, weights=w, k=1)[0]
        return pattern.format(city=city, state=state, jurisdiction=jurisdiction, office_type=office_type)

    # Helper: load hours-related weighted datasets once per call site
    def load_hours_datasets(self):
        start = Path(__file__)
        wd_path = dataset_path("public_sector", "administration", f"weekdays_{self._dataset}.csv", start=start)
        weekdays, wd_w = FileUtil.read_wgt_file(wd_path)
        open_path = dataset_path("public_sector", "administration", f"open_times_{self._dataset}.csv", start=start)
        opens, open_w = FileUtil.read_wgt_file(open_path)
        close_path = dataset_path("public_sector", "administration", f"close_times_{self._dataset}.csv", start=start)
        closes, close_w = FileUtil.read_wgt_file(close_path)
        ext_close_path = dataset_path(
            "public_sector", "administration", f"extended_close_times_{self._dataset}.csv", start=start
        )
        ext_closes, ext_close_w = FileUtil.read_wgt_file(ext_close_path)
        sat_open_path = dataset_path(
            "public_sector", "administration", f"saturday_open_times_{self._dataset}.csv", start=start
        )
        sat_opens, sat_open_w = FileUtil.read_wgt_file(sat_open_path)
        sat_close_path = dataset_path(
            "public_sector", "administration", f"saturday_close_times_{self._dataset}.csv", start=start
        )
        sat_closes, sat_close_w = FileUtil.read_wgt_file(sat_close_path)
        return (
            weekdays,
            wd_w,
            opens,
            open_w,
            closes,
            close_w,
            ext_closes,
            ext_close_w,
            sat_opens,
            sat_open_w,
            sat_closes,
            sat_close_w,
        )

    # Helper: founding year based on office type ranges (deterministic via rng)
    def pick_founding_year(self, office_type: str, *, now_year: int | None = None) -> int:
        year = now_year or __import__("datetime").datetime.now().year
        if "Federal" in office_type:
            min_age, max_age = 20, 200
        elif "State" in office_type:
            min_age, max_age = 15, 150
        elif "County" in office_type:
            min_age, max_age = 10, 100
        else:
            min_age, max_age = 5, 75
        return year - self._rng.randint(min_age, max_age)

    # Helper: pick staff count deterministically by office type
    def pick_staff_count(self, office_type: str) -> int:
        if "Federal" in office_type:
            return self._rng.randint(50, 500)
        if "State" in office_type:
            return self._rng.randint(30, 300)
        if "County" in office_type:
            return self._rng.randint(20, 150)
        if "Municipal" in office_type or "City" in office_type:
            return self._rng.randint(10, 100)
        return self._rng.randint(5, 75)

    # Helper: services from agencies dataset
    def pick_services(self, *, start: Path) -> list[str]:
        # Agencies file is headered; pick by weight and return names
        header, rows = FileUtil.read_csv_to_dict_of_tuples_with_header(
            dataset_path("public_sector", "administration", f"agencies_{self._dataset}.csv", start=start),
            ",",
        )
        name_idx = header.get("name")
        w_idx = header.get("weight")
        if name_idx is None or w_idx is None:
            # Fallback to headerless interpretation if structure unexpected
            from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

            values, w = load_weighted_values_try_dataset(
                "public_sector", "administration", "agencies.csv", dataset=self._dataset, start=start
            )
            k = self._rng.randint(5, min(10, len(values)))
            return sorted(values if k >= len(values) else self._rng.sample(list(values), k))
        # Build weighted list of names
        names = [r[name_idx] for r in rows]
        weights = [float(r[w_idx]) for r in rows]
        k = self._rng.randint(5, min(10, len(names)))
        if k >= len(names):
            return sorted(names)
        # Sample without replacement approximately, using simple loop
        pool = list(zip(names, weights, strict=False))
        selected: list[str] = []
        for _ in range(k):
            vals = [n for n, _ in pool]
            wgts = [w for _, w in pool]
            choice = self._rng.choices(vals, weights=wgts, k=1)[0]
            selected.append(choice)
            pool = [(n, w) for (n, w) in pool if n != choice]
            if not pool:
                break
        return sorted(selected)

    # Helper: departments from roles dataset
    def pick_departments(self, *, start: Path) -> list[str]:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        values, w = load_weighted_values_try_dataset(
            "public_sector", "administration", "roles.csv", dataset=self._dataset, start=start
        )
        k = self._rng.randint(3, min(7, len(values)))
        if k >= len(values):
            return sorted(values)
        return sorted(self._rng.sample(list(values), k))

    # Helper: leadership roles mapped to generated names
    def build_leadership(self, *, start: Path) -> dict[str, str]:
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        roles, w = load_weighted_values_try_dataset(
            "public_sector", "administration", "roles.csv", dataset=self._dataset, start=start
        )
        k = self._rng.randint(2, min(5, len(roles)))
        chosen = roles if k >= len(roles) else self._rng.sample(list(roles), k)
        leadership: dict[str, str] = {}
        for role in chosen:
            fname = self._given_name_generator.generate()
            lname = self._family_name_generator.generate()
            leadership[str(role)] = f"{fname} {lname}"
        return leadership

    # Helper: website builder; choose suffix by dataset for extensibility
    def build_website(self, jurisdiction: str) -> str:
        # Build domain via dataset-driven DomainGenerator to avoid static TLD mappings
        from datamimic_ce.domains.common.literal_generators.domain_generator import DomainGenerator

        domain = DomainGenerator(dataset=self._dataset, rng=self._rng).generate().lower()
        return f"https://www.{domain}"

    # Helper: email builder from dataset roles; local-part from role slug
    def build_email(self, office_type: str, website_url: str, *, start: Path) -> str:
        # Use roles dataset to derive a local-part; domain is derived from dataset-driven website
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        roles, w = load_weighted_values_try_dataset(
            "public_sector", "administration", "roles.csv", dataset=self._dataset, start=start
        )
        role = self._rng.choices(roles, weights=w, k=1)[0] if roles else "info"
        local = "".join(ch for ch in str(role).lower() if ch.isalnum()) or "info"
        domain = website_url.replace("https://www.", "")
        return f"{local}@{domain}"
