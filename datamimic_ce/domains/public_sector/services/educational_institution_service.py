# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Educational institution service.

This module provides a service for working with EducationalInstitution entities.
"""

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.public_sector.generators.educational_institution_generator import (
    EducationalInstitutionGenerator,
)
from datamimic_ce.domains.public_sector.models.educational_institution import EducationalInstitution


class EducationalInstitutionService(BaseDomainService[EducationalInstitution]):
    """Service for working with EducationalInstitution entities.

    This class provides methods for generating, exporting, and working with
    EducationalInstitution entities.
    """

    def __init__(self, dataset: str | None = None):
        super().__init__(EducationalInstitutionGenerator(dataset=dataset), EducationalInstitution)
