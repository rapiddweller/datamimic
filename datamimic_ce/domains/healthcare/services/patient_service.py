# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Patient service.

This module provides the PatientService class for generating and managing patient data.
"""

from random import Random

from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.healthcare.generators.patient_generator import PatientGenerator
from datamimic_ce.domains.healthcare.models.patient import Patient


class PatientService(BaseDomainService[Patient]):
    """Service for generating and managing patient data.

    This class provides methods for generating patient data, exporting it to various formats,
    and retrieving patients with specific characteristics.
    """

    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        demographic_sampler: DemographicSampler | None = None,
        rng: Random | None = None,
    ):
        # Thread demographic and RNG overrides through the service layer.
        super().__init__(
            PatientGenerator(
                dataset=dataset,
                demographic_config=demographic_config,
                demographic_sampler=demographic_sampler,
                rng=rng,
            ),
            Patient,
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "healthcare/medical/blood_types_{CC}.csv",
            "healthcare/medical/emergency_relationships_{CC}.csv",
            "healthcare/medical/allergies_{CC}.csv",
            "healthcare/medical/medications_{CC}.csv",
            "healthcare/medical/insurance_providers_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
