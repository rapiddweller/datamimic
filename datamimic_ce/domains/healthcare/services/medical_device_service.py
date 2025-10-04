# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from random import Random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.healthcare.generators.medical_device_generator import MedicalDeviceGenerator
from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice


class MedicalDeviceService(BaseDomainService[MedicalDevice]):
    """Service for managing medical device data.

    This class provides methods to create, retrieve, and manage medical device data.
    It integrates the model, data loader, and generator components.
    """

    def __init__(
        self,
        dataset: str | None = None,
        demographic_config: DemographicConfig | None = None,
        rng: Random | None = None,
    ):
        """Initialize the MedicalDeviceService.

        Args:
            dataset: The dataset to use for generating medical device data.
        """
        import random as _r

        super().__init__(
            MedicalDeviceGenerator(dataset=dataset, demographic_config=demographic_config, rng=rng or _r.Random()),
            MedicalDevice,
        )

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "healthcare/medical/device_types_{CC}.csv",
            "healthcare/medical/manufacturers_{CC}.csv",
            "healthcare/medical/device_statuses_{CC}.csv",
            "healthcare/medical/locations_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
