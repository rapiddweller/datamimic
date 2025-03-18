# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# from typing import List, Dict, Any, Optional

from datamimic_ce.domain_core.base_domain_service import BaseDomainService
from datamimic_ce.domains.common.generators.company_generator import CompanyGenerator
from datamimic_ce.domains.common.models.company import Company


class CompanyService(BaseDomainService[Company]):
    """Service for managing company data.

    This class provides methods for creating, retrieving, and managing company data.
    """
    def __init__(self, dataset: str | None = None):
        super().__init__(CompanyGenerator(dataset=dataset), Company)       
