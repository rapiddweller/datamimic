# # DATAMIMIC
# # Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# from typing import List, Dict, Any, Optional

from datamimic_ce.domains.common.generators.company_generator import CompanyGenerator
from datamimic_ce.domains.common.models.company import Company
from datamimic_ce.domains.domain_core import BaseDomainService


class CompanyService(BaseDomainService[Company]):
    """Service for managing company data.

    This class provides methods for creating, retrieving, and managing company data.
    """

    def __init__(self, dataset: str | None = None):
        super().__init__(CompanyGenerator(dataset=dataset), Company)

    @staticmethod
    def supported_datasets() -> set[str]:
        from pathlib import Path

        from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets

        patterns = [
            "common/organization/sector_{CC}.csv",
            "common/organization/legalForm_{CC}.csv",
            "common/net/webmailDomain_{CC}.csv",
            "common/net/tld_{CC}.csv",
        ]
        return compute_supported_datasets(patterns, start=Path(__file__))
