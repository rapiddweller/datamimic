# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.healthcare.generators.medical_device_generator import MedicalDeviceGenerator
from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice


class MedicalDeviceService(BaseDomainService[MedicalDevice]):
    """Service for managing medical device data.

    This class provides methods to create, retrieve, and manage medical device data.
    It integrates the model, data loader, and generator components.
    """

    def __init__(self, dataset: str | None = None):
        """Initialize the MedicalDeviceService.

        Args:
            dataset: The dataset to use for generating medical device data.
        """
        super().__init__(MedicalDeviceGenerator(dataset=dataset), MedicalDevice)
