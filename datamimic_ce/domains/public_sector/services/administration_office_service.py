# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office service.

This module provides a service for working with AdministrationOffice entities.
"""

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice


class AdministrationOfficeService(BaseDomainService[AdministrationOffice]):
    """Service for working with AdministrationOffice entities.

    This class provides methods for generating, exporting, and working with
    AdministrationOffice entities.
    """

    def __init__(self, dataset: str | None = None):
        super().__init__(AdministrationOfficeGenerator(dataset=dataset), AdministrationOffice)
