# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Doctor service.

This module provides a service for working with Doctor entities.
"""

from random import Random

from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.healthcare.generators.doctor_generator import DoctorGenerator
from datamimic_ce.domains.healthcare.models.doctor import Doctor


class DoctorService(BaseDomainService[Doctor]):
    """Service for working with Doctor entities.

    This class provides methods for generating, exporting, and working with
    Doctor entities.
    """

    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
        rng: Random | None = None,
    ) -> None:
        import random as _r

        super().__init__(
            DoctorGenerator(
                dataset=dataset,
                rng=rng or _r.Random(),
                demographic_config=demographic_config,
                demographic_sampler=demographic_sampler,
            ),
            Doctor,
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        return compute_supported_datasets(["healthcare/medical/specialties_{CC}.csv"], start=Path(__file__))
