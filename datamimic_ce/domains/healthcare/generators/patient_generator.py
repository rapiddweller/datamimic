# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Patient generator utilities."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from functools import cache
from pathlib import Path
from random import Random

from datamimic_ce.domains.common.demographics.sampler import DemographicSample, DemographicSampler
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.literal_generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.domains.common.literal_generators.given_name_generator import GivenNameGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset, pick_one_weighted
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil

_CONDITION_DATA_DIR = dataset_path("healthcare", "medical", start=Path(__file__))
# Directory for emergency relationships CSVs; test may monkeypatch this.
_EMERGENCY_RELATIONSHIP_DIR = dataset_path("healthcare", "medical", start=Path(__file__))


class PatientGenerator(BaseDomainGenerator):
    # Cache for loaded emergency relationship distributions per dataset
    _emergency_relationship_cache: dict[str, tuple[list[str], list[float]]] = {}

    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
        rng: Random | None = None,
    ):
        self._dataset = dataset or "US"
        self._rng: Random = rng or Random()
        self._demographic_config = (demographic_config or DemographicConfig()).with_defaults()
        self._person_generator = PersonGenerator(
            dataset=self._dataset,
            demographic_config=self._demographic_config,
            demographic_sampler=demographic_sampler,
            rng=self._rng,
        )
        self._demographic_sampler = demographic_sampler
        # Fan out deterministic RNG so seeded patient cohorts remain reproducible across dependent literals.
        self._family_name_generator = FamilyNameGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._given_name_generator = GivenNameGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        self._phone_number_generator = PhoneNumberGenerator(
            dataset=self._dataset,
            rng=self._derive_rng() if rng is not None else None,
        )
        # Track last blood type to reduce immediate repetition in tests
        self._last_blood_type: str | None = None

    @property
    def person_generator(self) -> PersonGenerator:
        """Get the person generator.

        Returns:
            The person generator.
        """
        return self._person_generator

    @property
    def demographic_config(self) -> DemographicConfig:
        """Expose the demographic overrides applied to this generator."""

        return self._demographic_config

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def rng(self) -> Random:
        return self._rng

    def _derive_rng(self) -> Random:
        # Spawn child RNGs from the base seed so seeded cohorts remain reproducible without sharing streams.
        return Random(self._rng.randrange(2**63)) if isinstance(self._rng, Random) else Random()

    # Helper: pick blood type with anti-repeat
    def pick_blood_type(self, *, start_path: str | None = None) -> str:
        start = Path(start_path) if start_path else Path(__file__)
        values, weights = load_weighted_values_try_dataset(
            "healthcare", "medical", "blood_types.csv", dataset=self._dataset, start=start
        )
        choice = pick_one_weighted(self._rng, values, weights)
        last = getattr(self, "_last_blood_type", None)
        if last == choice and len(values) > 1:
            choice = pick_one_weighted(self._rng, values, weights)
        self._last_blood_type = choice
        return choice

    def generate_age_appropriate_conditions(
        self, age: int, demographic_sample: DemographicSample | None = None
    ) -> list[str]:
        """Generate weighted medical conditions for the given age."""

        base_weights = _load_condition_base_weights(self._dataset)
        include = self._demographic_config.normalized_includes()
        exclude = self._demographic_config.normalized_excludes()
        if demographic_sample is not None and demographic_sample.conditions:
            selections = [
                condition
                for condition in demographic_sample.conditions
                if condition.lower() not in {name.lower() for name in exclude}
            ]
            normalized_includes = {name.lower(): name for name in include}
            present = {name.lower() for name in selections}
            for key, original in normalized_includes.items():
                if key not in present and key not in {name.lower() for name in exclude}:
                    selections.append(original)
            # Deterministic ordering keeps tests stable when sampler emits frozensets.
            return sorted(selections)
        if not base_weights:
            return []
        #  Apply age multipliers while keeping CSV as the single source of names and base weights.
        weighted = _apply_age_adjustments(base_weights, age, self._dataset)
        weighted = _apply_condition_filters(weighted, include, exclude)
        if not weighted:
            return []
        count_weights = self._condition_count_weights(age)
        num_conditions = self._rng.choices([0, 1, 2, 3, 4], weights=count_weights, k=1)[0]
        if include and num_conditions == 0:
            num_conditions = 1
        if num_conditions == 0:
            return []
        selections = self._sample_unique_conditions(weighted, num_conditions)
        missing_includes = [name for name in include if name and name.lower() not in {s.lower() for s in selections}]
        for name in missing_includes:
            selections.append(name)
        return selections

    def _condition_count_weights(self, age: int) -> list[float]:
        """Return the count distribution for conditions based on age."""

        #  Preserve legacy distribution so existing cohorts behave consistently.
        if age < 18:
            return [0.8, 0.15, 0.04, 0.01, 0.0]
        if age < 40:
            return [0.6, 0.25, 0.1, 0.04, 0.01]
        if age < 65:
            return [0.4, 0.3, 0.15, 0.1, 0.05]
        return [0.2, 0.3, 0.25, 0.15, 0.1]

    def _sample_unique_conditions(self, weights: dict[str, float], count: int) -> list[str]:
        """Sample without replacement according to normalized weights."""

        remaining = dict(weights)
        selections: list[str] = []
        for _ in range(min(count, len(remaining))):
            options = list(remaining.keys())
            option_weights = [remaining[name] for name in options]
            choice = self._rng.choices(options, weights=option_weights, k=1)[0]
            selections.append(choice)
            #  Remove the selection to avoid rejection-sampling loops.
            del remaining[choice]
        return selections

    def generate_insurance_provider(self) -> str:
        """Generate a random insurance provider.

        Returns:
            A random insurance provider.
        """
        file_path = dataset_path(
            "healthcare", "medical", f"insurance_providers_{self._dataset}.csv", start=Path(__file__)
        )
        loaded_data = FileUtil.read_weight_csv(file_path)
        # Reuse the injected RNG to keep sampling reproducible under tests.
        return self._rng.choices(loaded_data[0], weights=loaded_data[1], k=1)[0]  # type: ignore

    def get_allergies(self) -> list[str]:
        # Determine how many allergies to generate (most people have 0-3)
        num_allergies = self._rng.choices(
            [0, 1, 2, 3, 4, 5],
            weights=[0.5, 0.2, 0.15, 0.1, 0.03, 0.02],
            k=1,
        )[0]

        if num_allergies == 0:
            return []

        file_path = dataset_path("healthcare", "medical", f"allergies_{self._dataset}.csv", start=Path(__file__))
        wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")

        # Sample allergies with consistent randomness for downstream assertions.
        random_choices = self._rng.choices(loaded_data, weights=wgt, k=num_allergies)
        return [choice["allergen"] for choice in random_choices]

    def get_medications(self, age: int) -> list[str]:
        # Determine how many medications to generate
        # Older people tend to take more medications
        if age < 18:
            weights = [0.7, 0.2, 0.08, 0.02, 0.0, 0.0]
        elif age < 40:
            weights = [0.5, 0.3, 0.15, 0.04, 0.01, 0.0]
        elif age < 65:
            weights = [0.3, 0.3, 0.2, 0.1, 0.07, 0.03]
        else:
            weights = [0.1, 0.2, 0.3, 0.2, 0.15, 0.05]

        num_medications = self._rng.choices([0, 1, 2, 3, 4, 5], weights=weights, k=1)[0]

        if num_medications == 0:
            return []

        file_path = dataset_path("healthcare", "medical", f"medications_{self._dataset}.csv", start=Path(__file__))
        wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")

        # Align medication sampling with the shared RNG for deterministic seeds.
        random_choices = self._rng.choices(loaded_data, weights=wgt, k=num_medications)
        return [choice["name"] for choice in random_choices]

    def get_emergency_contact(self, family_name: str) -> dict[str, str]:
        """Generate a random emergency contact.

        Returns:
            A dictionary containing emergency contact information.
        """
        # Generate a name for the emergency contact
        given_name = self._given_name_generator.generate()

        # 50% chance the emergency contact has the same family name
        family_name = self._family_name_generator.generate() if self._rng.random() < 0.5 else family_name

        # Generate a relationship using weighted CSV if available, with caching
        values, weights = _load_emergency_relationships(self._dataset)
        relationship = self._rng.choices(values, weights=weights, k=1)[0] if values else "Friend"
        phone_number = self._phone_number_generator.generate()

        return {"name": f"{given_name} {family_name}", "relationship": relationship, "phone": phone_number}


@cache
def _load_condition_base_weights(dataset: str) -> dict[str, float]:
    """Load and normalize condition weights for a dataset."""

    candidates = [
        f"condition_weights_{dataset}.csv",
        f"medical_conditions_{dataset}.csv",
    ]
    for candidate in candidates:
        path = _CONDITION_DATA_DIR / candidate
        if path.exists():
            break
    else:
        return {}
    weights: dict[str, float] = {}
    for row in _iter_csv_dicts(path):
        condition = (row.get("condition") or "").strip()
        if not condition:
            continue
        weight_raw = row.get("base_weight") or row.get("weight") or row.get("Weight")
        if weight_raw is None:
            continue
        try:
            weights[condition] = float(weight_raw)
        except ValueError:
            continue
    total = sum(weights.values())
    if total <= 0:
        return weights
    # Normalize to keep reweighting steps numerically stable.
    return {key: value / total for key, value in weights.items()}


@cache
def _load_condition_age_weights(dataset: str) -> tuple[tuple[str, int, int, float], ...]:
    """Load optional age multipliers for conditions."""

    path = _CONDITION_DATA_DIR / f"condition_age_weights_{dataset}.csv"
    if not path.exists():
        return tuple()
    entries: list[tuple[str, int, int, float]] = []
    for row in _iter_csv_dicts(path):
        condition = (row.get("condition") or "").strip()
        if not condition:
            continue
        try:
            age_min = int((row.get("age_min") or "0").strip())
            age_max_raw = row.get("age_max")
            age_max = int(age_max_raw.strip()) if age_max_raw and age_max_raw.strip() else 200
            multiplier = float((row.get("weight_multiplier") or "1").strip())
        except (ValueError, AttributeError):
            continue
        entries.append((condition, age_min, age_max, multiplier))
    return tuple(entries)


def _apply_age_adjustments(weights: dict[str, float], age: int, dataset: str) -> dict[str, float]:
    """Apply dataset-specific age multipliers to the weights."""

    adjusted = dict(weights)
    for condition, age_min, age_max, multiplier in _load_condition_age_weights(dataset):
        if condition not in adjusted:
            continue
        if age_min <= age <= age_max:
            adjusted[condition] *= multiplier
    return adjusted


def _apply_condition_filters(
    weights: dict[str, float],
    include: Iterable[str],
    exclude: Iterable[str],
) -> dict[str, float]:
    """Apply include/exclude filters and renormalize."""

    normalized_lookup = {name.lower(): name for name in weights}
    exclude_keys = {name.lower() for name in exclude}
    filtered = {name: value for name, value in weights.items() if name.lower() not in exclude_keys}
    if not filtered and include:
        filtered = {
            normalized_lookup.get(name.lower(), name): 0.0 for name in include if name.lower() not in exclude_keys
        }
    positive_min = min((value for value in filtered.values() if value > 0), default=1.0)
    # Ensure include-only conditions have a non-negligible chance
    epsilon = positive_min if positive_min > 0 else 1.0
    for name in include:
        key = name.lower()
        if key in exclude_keys:
            continue
        canonical = normalized_lookup.get(key, name)
        filtered.setdefault(canonical, epsilon)
    total = sum(filtered.values())
    if total <= 0:
        size = len(filtered)
        if size == 0:
            return {}
        uniform = 1.0 / size
        # Fallback to uniform distribution when all weights cancel out.
        return {name: uniform for name in filtered}
    return {name: value / total for name, value in filtered.items()}


def _iter_csv_dicts(path: Path) -> Iterable[dict[str, str]]:
    """Yield CSV rows as dictionaries while skipping header comments."""

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(_strip_comments(handle))
        for row in reader:
            yield {key: value for key, value in row.items() if key is not None}


def _strip_comments(lines: Iterable[str]) -> Iterable[str]:
    """Filter out commented lines from a CSV stream."""

    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        yield line


def _load_emergency_relationships(dataset: str) -> tuple[list[str], list[float]]:
    """Load emergency relationship distribution for a dataset with memoization.

    The CSV format is expected to be two columns: label,weight without header.
    Tests monkeypatch `_EMERGENCY_RELATIONSHIP_DIR` to a temp dir.
    """
    cache = PatientGenerator._emergency_relationship_cache
    if dataset in cache:
        return cache[dataset]

    # Use dataset_path so US fallback and single-warning logging is applied consistently
    path = dataset_path("healthcare", "medical", f"emergency_relationships_{dataset}.csv", start=Path(__file__))
    values, weights = FileUtil.read_wgt_file(file_path=path)

    cache[dataset] = (values, weights)
    return values, weights
