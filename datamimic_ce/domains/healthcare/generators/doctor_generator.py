# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor generator utilities.

This module provides utility functions for generating doctor data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
    from datamimic_ce.domains.common.models.demographic_config import DemographicConfig

import random
from pathlib import Path

from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.healthcare.generators.hospital_generator import HospitalGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class DoctorGenerator(BaseDomainGenerator):
    """Generate doctor data."""

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
    ):
        #  normalize dataset to ISO-3166 alpha-2 and keep lookup consistent
        self._dataset = (dataset or "US").upper()
        self._rng: random.Random = rng or random.Random()
        from datamimic_ce.domains.common.models.demographic_config import DemographicConfig as _DC

        demo = demographic_config if demographic_config is not None else _DC()
        self._person_generator = PersonGenerator(
            dataset=self._dataset,
            demographic_config=demo,
            demographic_sampler=demographic_sampler,
            rng=self._rng,
            min_age=25,
        )
        self._hospital_generator = HospitalGenerator(dataset=self._dataset, rng=self._rng)
        self._last_specialty: str | None = None
        self._last_med_school: str | None = None
        self._last_grad_year: int | None = None

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    @property
    def hospital_generator(self) -> HospitalGenerator:
        return self._hospital_generator

    @property
    def rng(self) -> random.Random:
        return self._rng

    def generate_specialty(self) -> str:
        """Generate a medical specialty.

        Returns:
            A medical specialty.
        """
        file_path = dataset_path("healthcare", "medical", f"specialties_{self._dataset}.csv", start=Path(__file__))
        wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        values = [item["specialty"] for item in loaded_data]
        # Avoid immediate repetition
        if self._last_specialty in values and len(values) > 1:
            pool = [(v, float(w)) for v, w in zip(values, wgt, strict=False) if v != self._last_specialty]
            vals, wgts = zip(*pool, strict=False)
            choice = self._rng.choices(list(vals), weights=list(wgts))[0]
        else:
            choice = self._rng.choices(values, weights=wgt)[0]
        self._last_specialty = choice
        return choice

    def generate_medical_school(self) -> str:
        """Generate a medical school.

        Returns:
            A medical school.
        """
        #  prefer dataset-specific medical_schools; gracefully fallback to institutions datasets
        try:
            path = dataset_path("healthcare", "medical", f"medical_schools_{self._dataset}.csv", start=Path(__file__))
            values, w = FileUtil.read_wgt_file(path)
        except FileNotFoundError:
            try:
                inst_path = dataset_path(
                    "healthcare", "medical", f"institutions_{self._dataset}.csv", start=Path(__file__)
                )
                values, w = FileUtil.read_wgt_file(inst_path)
            except FileNotFoundError:
                # final fallback: US institutions if present
                inst_us = dataset_path("healthcare", "medical", "institutions_US.csv", start=Path(__file__))
                values, w = FileUtil.read_wgt_file(inst_us)
        # Avoid immediate repetition when possible
        if self._last_med_school in values and len(values) > 1:
            pool = [(v, float(wi)) for v, wi in zip(values, w, strict=False) if v != self._last_med_school]
            p_vals, p_w = zip(*pool, strict=False)
            choice = self._rng.choices(list(p_vals), weights=list(p_w), k=1)[0]
        else:
            choice = self._rng.choices(values, weights=w, k=1)[0]
        self._last_med_school = choice
        return choice

    def generate_certifications(self) -> list[str]:
        """Generate a list of certifications.

        Returns:
            A list of certifications.
        """
        file_path = dataset_path("healthcare", "medical", f"certifications_{self._dataset}.csv", start=Path(__file__))
        wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        # choose 1-3 certifications
        k = self._rng.randint(1, 3)
        # simple weighted picks without replacement
        picks: list[str] = []
        pool = [(item["certification"], float(w)) for item, w in zip(loaded_data, wgt, strict=False)]
        for _ in range(min(k, len(pool))):
            values = [v for v, _ in pool]
            weights = [wt for _, wt in pool]
            chosen = self._rng.choices(values, weights=weights, k=1)[0]
            picks.append(chosen)
            pool = [(v, wt) for (v, wt) in pool if v != chosen]
        return picks

    # Helper to pick a graduation year with anti-repetition
    def pick_graduation_year(self, age: int, *, now_year: int | None = None) -> int:
        year_now = now_year or __import__("datetime").datetime.now().year
        min_after = 0
        max_after = max(0, min(45, age - 25))
        years_after = self._rng.randint(min_after, max_after)
        grad = year_now - years_after
        if self._last_grad_year is not None and max_after - min_after >= 1 and grad == self._last_grad_year:
            # nudge by +/- 1 year within bounds if possible
            alt = grad + 1 if grad + 1 <= year_now - min_after else grad - 1
            if alt >= year_now - max_after and alt <= year_now - min_after:
                grad = alt
        self._last_grad_year = grad
        return grad
