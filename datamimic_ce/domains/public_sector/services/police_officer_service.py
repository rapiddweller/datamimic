# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Police officer service.

This module provides a service for working with PoliceOfficer entities.
"""

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.public_sector.generators.police_officer_generator import PoliceOfficerGenerator
from datamimic_ce.domains.public_sector.models.police_officer import PoliceOfficer


class PoliceOfficerService(BaseDomainService[PoliceOfficer]):
    """Service for working with PoliceOfficer entities.

    This class provides methods for generating, exporting, and working with
    PoliceOfficer entities.
    """

    def __init__(self, dataset: str | None = None):
        super().__init__(PoliceOfficerGenerator(dataset=dataset), PoliceOfficer)
