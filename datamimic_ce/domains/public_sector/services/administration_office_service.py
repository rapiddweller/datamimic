# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Administration office service.

This module provides a service for working with AdministrationOffice entities.
"""

from random import Random

from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice


class AdministrationOfficeService(BaseDomainService[AdministrationOffice]):
    """Service for working with AdministrationOffice entities.

    This class provides methods for generating, exporting, and working with
    AdministrationOffice entities.
    """

    def __init__(self, dataset: str | None = None, rng: Random | None = None):
        super().__init__(AdministrationOfficeGenerator(dataset=dataset, rng=rng), AdministrationOffice)

    @staticmethod
    def supported_datasets() -> set[str]:
        """Return ISO dataset codes supported by all required datasets for this domain.

        WHY: Tests and callers may need to know which datasets are fully covered
        without relying on fallbacks.
        """
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "public_sector/administration/office_types_{CC}.csv",
            "public_sector/administration/jurisdictions_{CC}.csv",
            "public_sector/administration/name_patterns_{CC}.csv",
            "public_sector/administration/roles_{CC}.csv",
            "public_sector/administration/agencies_{CC}.csv",
            "public_sector/administration/weekdays_{CC}.csv",
            "public_sector/administration/open_times_{CC}.csv",
            "public_sector/administration/close_times_{CC}.csv",
            "public_sector/administration/extended_close_times_{CC}.csv",
            "public_sector/administration/saturday_open_times_{CC}.csv",
            "public_sector/administration/saturday_close_times_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
