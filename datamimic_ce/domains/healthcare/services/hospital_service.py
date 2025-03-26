# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Hospital service.

This module provides the HospitalService class for generating and managing hospital data.
"""

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.healthcare.generators.hospital_generator import HospitalGenerator
from datamimic_ce.domains.healthcare.models.hospital import Hospital


class HospitalService(BaseDomainService[Hospital]):
    """Service for generating and managing hospital data.

    This class provides methods for generating hospital data, exporting it to various formats,
    and retrieving hospitals with specific characteristics.
    """

    def __init__(self, dataset: str | None = None):
        super().__init__(HospitalGenerator(dataset), Hospital)
