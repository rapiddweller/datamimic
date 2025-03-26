# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.common.generators.city_generator import CityGenerator
from datamimic_ce.domains.common.models.city import City


class CityService(BaseDomainService[City]):
    """Service for managing city data.

    This class provides methods for creating, retrieving, and managing city data.
    """

    def __init__(self, dataset: str = "US"):
        super().__init__(CityGenerator(dataset), City)
