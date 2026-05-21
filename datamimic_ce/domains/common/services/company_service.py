# # DATAMIMIC
# # Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# from typing import List, Dict, Any, Optional

from random import Random

from datamimic_ce.domains.common.generators.company_generator import CompanyGenerator
from datamimic_ce.domains.common.models.company import Company
from datamimic_ce.domains.domain_core import BaseDomainService
from datamimic_ce.domains.domain_core.attribute_catalog import EntitySchema, FieldSpec, field

COMPANY_SCHEMA = EntitySchema(
    "Company",
    (
        field("short_name", str, "Short company name."),
        field("sector", str, "Business sector.", optional=True),
        field("email", str, "Company email address."),
        field("url", str, "Company website URL.", optional=True),
        field("phone_number", str, "General phone number.", optional=True),
        field("office_phone", str, "Office phone number.", optional=True),
        field("fax", str, "Fax number.", optional=True),
        field("street", str, "Street or thoroughfare name."),
        field("house_number", str, "House or building number."),
        field("city", str, "City or locality name."),
        field("state", str, "State, province, or region.", optional=True),
        field("zip_code", str, "Postal or ZIP code."),
        field("country", str, "Human-readable country name."),
        field("country_code", str, "ISO 3166-1 alpha-2 country code."),
    ),
)


class CompanyService(BaseDomainService[Company]):
    """Service for managing company data.

    This class provides methods for creating, retrieving, and managing company data.
    """

    DATASET_PATTERNS = (
        "common/organization/sector_{CC}.csv",
        "common/organization/legalForm_{CC}.csv",
        "common/net/webmailDomain_{CC}.csv",
        "common/net/tld_{CC}.csv",
    )

    def __init__(
        self,
        dataset: str | None = None,
        rng: Random | None = None,
    ):
        super().__init__(CompanyGenerator(dataset=dataset, rng=rng), Company)

    @classmethod
    def attribute_specs(cls) -> tuple[FieldSpec, ...]:
        return COMPANY_SCHEMA.fields
