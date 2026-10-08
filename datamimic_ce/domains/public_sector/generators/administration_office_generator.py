# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office generator utilities.

This module provides utility functions for generating administration office data.
"""

import datetime
import random
from pathlib import Path
from typing import TypeVar

from datamimic_ce.domains.domain_core.base_domain_generator import ClockAnchoredDomainGenerator
from datamimic_ce.domains.domain_core.datasets.path import dataset_path
from datamimic_ce.domains.shared.datasets.loader import (
    load_weighted_values_try_dataset,
    pick_one_weighted_no_repeat,
    read_headered_csv,
    read_weighted_values,
)
from datamimic_ce.domains.shared.generators.address_generator import AddressGenerator
from datamimic_ce.domains.shared.generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.shared.literal_generators.person.family_name_generator import FamilyNameGenerator
from datamimic_ce.domains.shared.literal_generators.person.given_name_generator import GivenNameGenerator

T = TypeVar("T")  # Define a type variable for generic typing


class AdministrationOfficeGenerator(ClockAnchoredDomainGenerator):
    """Generator for administration office data."""

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        reference_now: datetime.datetime | None = None,
    ):
        """Initialize the administration office generator.

        Args:
            dataset: The country code to use for data generation
            rng: Optional seeded random instance for deterministic output.
            reference_now: Optional fixed datetime anchor for deterministic mode.
        """
        super().__init__(dataset=dataset, rng=rng, reference_now=reference_now)
        # Derive child RNGs so seeded administration offices replay deterministic nested attributes.
        self._address_generator = AddressGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )
        self._phone_number_generator = PhoneNumberGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )
        self._family_name_generator = FamilyNameGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )
        self._given_name_generator = GivenNameGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
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

    def generate_office_id_candidate(self) -> str:
        rng = self.rng
        suffix = "".join(rng.choice("0123456789ABCDEF") for _ in range(8))
        return f"ADM-{suffix}"

    @property
    def last_hours_signature(self) -> tuple[tuple[str, str], ...] | None:
        """Signature of the previously generated hours, for cross-entity anti-repeat."""
        return self._last_hours_signature

    @last_hours_signature.setter
    def last_hours_signature(self, sig: tuple[tuple[str, str], ...]) -> None:
        self._last_hours_signature = sig

    # Helper: pick office type from dataset using weighted values with anti-repeat
    def pick_office_type(self) -> str:
        values, weights = load_weighted_values_try_dataset(
            "public_sector",
            "administration",
            "office_types.csv",
            dataset=self._dataset,
            start=Path(__file__),
        )
        choice = pick_one_weighted_no_repeat(self._rng, values, weights, last=self._last_office_type)
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
        pick = pick_one_weighted_no_repeat(self._rng, values, weights, last=self._last_jurisdiction)
        self._last_jurisdiction = pick
        return pick.lower()

    def generate_jurisdiction(self, office_type: str, city: str, state: str) -> str:
        if "Municipal" in office_type or "City" in office_type:
            return f"City of {city}"
        elif "County" in office_type:
            return f"{city} County"
        elif "State" in office_type:
            return f"State of {state}"
        elif "Federal" in office_type:
            return "Federal"

        pick = self.pick_jurisdiction_bucket()
        if pick == "city":  # noqa: SIM116 - format only the selected jurisdiction
            return f"City of {city}"
        elif pick == "county":
            return f"{city} County"
        elif pick == "state":
            return f"State of {state}"
        return "Federal"

    # Helper: build office name using dataset patterns (US fallback handled by dataset_path)
    def build_office_name(self, city: str, state: str, office_type: str, jurisdiction: str) -> str:
        from datamimic_ce.domains.shared.datasets.loader import load_weighted_values_try_dataset

        patterns, w = load_weighted_values_try_dataset(
            "public_sector", "administration", "name_patterns.csv", dataset=self._dataset, start=Path(__file__)
        )
        pattern = self._rng.choices(patterns, weights=w, k=1)[0]
        return pattern.format(city=city, state=state, jurisdiction=jurisdiction, office_type=office_type)

    # Helper: load hours-related weighted datasets once per call site
    def load_hours_datasets(self):
        start = Path(__file__)
        wd_path = dataset_path("public_sector", "administration", f"weekdays_{self._dataset}.csv", start=start)
        weekdays, wd_w = read_weighted_values(wd_path)
        open_path = dataset_path("public_sector", "administration", f"open_times_{self._dataset}.csv", start=start)
        opens, open_w = read_weighted_values(open_path)
        close_path = dataset_path("public_sector", "administration", f"close_times_{self._dataset}.csv", start=start)
        closes, close_w = read_weighted_values(close_path)
        ext_close_path = dataset_path(
            "public_sector", "administration", f"extended_close_times_{self._dataset}.csv", start=start
        )
        ext_closes, ext_close_w = read_weighted_values(ext_close_path)
        sat_open_path = dataset_path(
            "public_sector", "administration", f"saturday_open_times_{self._dataset}.csv", start=start
        )
        sat_opens, sat_open_w = read_weighted_values(sat_open_path)
        sat_close_path = dataset_path(
            "public_sector", "administration", f"saturday_close_times_{self._dataset}.csv", start=start
        )
        sat_closes, sat_close_w = read_weighted_values(sat_close_path)
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

    def generate_hours_of_operation(self) -> dict[str, str]:
        """Generate operating hours and retain the cross-office anti-repeat signature."""
        (
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
        ) = self.load_hours_datasets()

        hours: dict[str, str] = {}

        # Keep dataset loading before the shared RNG is accessed.
        rng = self.rng
        standard_open = rng.choices(opens, weights=open_w, k=1)[0]
        standard_close = rng.choices(closes, weights=close_w, k=1)[0]

        for day in weekdays:
            hours[day] = f"{standard_open} - {standard_close}"

        if rng.random() < 0.3:
            extended_day = rng.choices(weekdays, weights=wd_w, k=1)[0]
            extended_close = rng.choices(ext_closes, weights=ext_close_w, k=1)[0]
            hours[extended_day] = f"{standard_open} - {extended_close}"

        if rng.random() < 0.2:
            saturday_open = rng.choices(sat_opens, weights=sat_open_w, k=1)[0]
            saturday_close = rng.choices(sat_closes, weights=sat_close_w, k=1)[0]
            hours["Saturday"] = f"{saturday_open} - {saturday_close}"
        else:
            hours["Saturday"] = "Closed"

        hours["Sunday"] = "Closed"

        signature = tuple(sorted(hours.items()))
        if self.last_hours_signature == signature:
            candidates = [day for day, value in hours.items() if value != "Closed"]
            if candidates:
                extended_day = rng.choice(candidates)
                extended_close = rng.choices(ext_closes, weights=ext_close_w, k=1)[0]
                hours[extended_day] = f"{standard_open} - {extended_close}"
            else:
                saturday_open = rng.choices(sat_opens, weights=sat_open_w, k=1)[0]
                saturday_close = rng.choices(sat_closes, weights=sat_close_w, k=1)[0]
                hours["Saturday"] = f"{saturday_open} - {saturday_close}"
            signature = tuple(sorted(hours.items()))
        self.last_hours_signature = signature
        return hours

    def _founding_age_bounds(self, office_type: str) -> tuple[int, int]:
        if "Federal" in office_type:
            return 20, 200
        elif "State" in office_type:
            return 15, 150
        elif "County" in office_type:
            return 10, 100
        return 5, 75

    # Helper: founding year based on office type ranges (deterministic via rng)
    def pick_founding_year(self, office_type: str) -> int:
        year = self._reference_now.year
        min_age, max_age = self._founding_age_bounds(office_type)
        return year - self._rng.randint(min_age, max_age)

    def generate_founding_year(self, office_type: str, current_year: int) -> int:
        min_age, max_age = self._founding_age_bounds(office_type)
        return current_year - self.rng.randint(min_age, max_age)

    def get_email_department(self, office_type_lower: str) -> str:
        if "tax" in office_type_lower:
            return "tax"
        elif "motor" in office_type_lower or "dmv" in office_type_lower:
            return "dmv"
        elif "social" in office_type_lower or "welfare" in office_type_lower:
            return "socialservices"
        elif "permit" in office_type_lower or "licens" in office_type_lower:
            return "permits"
        elif "election" in office_type_lower:
            return "elections"
        elif "health" in office_type_lower:
            return "health"
        elif "housing" in office_type_lower:
            return "housing"
        elif "environment" in office_type_lower:
            return "environment"
        elif "planning" in office_type_lower or "development" in office_type_lower:
            return "planning"
        return "info"

    # Helper: pick staff count deterministically by office type, avoiding an
    # immediate repeat across consecutive entities (state owned here, not in the model).
    def pick_staff_count(self, office_type: str) -> int:
        def draw() -> int:
            if "Federal" in office_type:
                return self._rng.randint(50, 500)
            if "State" in office_type:
                return self._rng.randint(30, 300)
            if "County" in office_type:
                return self._rng.randint(20, 150)
            if "Municipal" in office_type or "City" in office_type:
                return self._rng.randint(10, 100)
            return self._rng.randint(5, 75)

        val = draw()
        if val == self._last_staff_count:
            val = draw()
        self._last_staff_count = val
        return val

    def generate_annual_budget(self, office_type: str, staff_count: int) -> int:
        rng = self.rng
        base_per_staff = rng.uniform(80000, 120000)

        if "Federal" in office_type:
            multiplier = rng.uniform(1.5, 3.0)
        elif "State" in office_type:
            multiplier = rng.uniform(1.2, 2.0)
        elif "County" in office_type:
            multiplier = rng.uniform(1.0, 1.5)
        else:
            multiplier = rng.uniform(0.8, 1.2)

        budget = staff_count * base_per_staff * multiplier
        budget *= rng.uniform(0.9, 1.1)
        return round(budget / 1000) * 1000

    # Helper: services from agencies dataset
    def pick_services(self, *, start: Path) -> list[str]:
        # Agencies file is headered; pick by weight and return names
        header, rows = read_headered_csv(
            dataset_path("public_sector", "administration", f"agencies_{self._dataset}.csv", start=start),
            ",",
        )
        name_idx = header.get("name")
        w_idx = header.get("weight")
        if name_idx is None or w_idx is None:
            # Fallback to headerless interpretation if structure unexpected
            from datamimic_ce.domains.shared.datasets.loader import load_weighted_values_try_dataset

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
        from datamimic_ce.domains.shared.datasets.loader import load_weighted_values_try_dataset

        values, w = load_weighted_values_try_dataset(
            "public_sector", "administration", "roles.csv", dataset=self._dataset, start=start
        )
        k = self._rng.randint(3, min(7, len(values)))
        if k >= len(values):
            return sorted(values)
        return sorted(self._rng.sample(list(values), k))

    # Helper: leadership roles mapped to generated names
    def build_leadership(self, *, start: Path) -> dict[str, str]:
        from datamimic_ce.domains.shared.datasets.loader import load_weighted_values_try_dataset

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
        from datamimic_ce.domains.shared.literal_generators.contact.domain_generator import DomainGenerator

        domain_generator = DomainGenerator(dataset=self._dataset, rng=self._derive_rng())
        domain = domain_generator.generate().lower()
        return f"https://www.{domain}"

    # Helper: email builder from dataset roles; local-part from role slug
    def build_email(self, office_type: str, website_url: str, *, start: Path) -> str:
        # Use roles dataset to derive a local-part; domain is derived from dataset-driven website
        from datamimic_ce.domains.shared.datasets.loader import load_weighted_values_try_dataset

        roles, w = load_weighted_values_try_dataset(
            "public_sector", "administration", "roles.csv", dataset=self._dataset, start=start
        )
        role = self._rng.choices(roles, weights=w, k=1)[0] if roles else "info"
        local = "".join(ch for ch in str(role).lower() if ch.isalnum()) or "info"
        domain = website_url.replace("https://www.", "")
        return f"{local}@{domain}"
