# # DATAMIMIC
# # Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# from typing import List, Dict, Any, Optional

import random

from datamimic_ce.domains.common.generators.company_generator import CompanyGenerator
from datamimic_ce.domains.common.models.company import Company
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import AttributeSpec, specs


class CompanyService(BaseDomainService[Company]):
    """Service for managing company data.

    This class provides methods for creating, retrieving, and managing company data.
    """

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__(CompanyGenerator(dataset=dataset, rng=rng), Company)

    @classmethod
    def attribute_specs(cls) -> tuple[AttributeSpec, ...]:
        return specs(
            ("short_name", "str", "Short company name."),
            ("sector", "str | None", "Business sector."),
            ("email", "str", "Company email address."),
            ("url", "str | None", "Company website URL."),
            ("phone_number", "str | None", "General phone number."),
            ("office_phone", "str | None", "Office phone number."),
            ("fax", "str | None", "Fax number."),
            ("street", "str", "Street or thoroughfare name."),
            ("house_number", "str", "House or building number."),
            ("city", "str", "City or locality name."),
            ("state", "str | None", "State, province, or region."),
            ("zip_code", "str", "Postal or ZIP code."),
            ("country", "str", "Human-readable country name."),
            ("country_code", "str", "ISO 3166-1 alpha-2 country code."),
        )

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
