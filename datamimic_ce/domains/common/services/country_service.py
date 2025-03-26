# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.common.generators.country_generator import CountryGenerator
from datamimic_ce.domains.common.models.country import Country


class CountryService(BaseDomainService[Country]):
    """Service for managing country data.

    This class provides methods for creating, retrieving, and managing country data.
    """

    def __init__(self):
        super().__init__(CountryGenerator(), Country)
