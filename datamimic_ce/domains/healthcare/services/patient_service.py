# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Patient service.

This module provides the PatientService class for generating and managing patient data.
"""

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.healthcare.generators.patient_generator import PatientGenerator
from datamimic_ce.domains.healthcare.models.patient import Patient


class PatientService(BaseDomainService[Patient]):
    """Service for generating and managing patient data.

    This class provides methods for generating patient data, exporting it to various formats,
    and retrieving patients with specific characteristics.
    """

    def __init__(self, dataset: str | None = None):
        super().__init__(PatientGenerator(dataset=dataset), Patient)
