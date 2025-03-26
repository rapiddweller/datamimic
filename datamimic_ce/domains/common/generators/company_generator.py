# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.literal_generators.sector_generator import SectorGenerator
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class CompanyGenerator(BaseDomainGenerator):
    """Generator for company-related attributes.

    Provides methods to generate company-related attributes such as
    company names, emails, URLs, and other information.
    """

    def __init__(self, dataset: str | None = None):
        self._dataset = dataset or "US"
        self._company_name_generator = CompanyNameGenerator()
        self._email_address_generator = EmailAddressGenerator(dataset=self._dataset)
        self._phone_number_generator = PhoneNumberGenerator(dataset=self._dataset)
        self._address_generator = AddressGenerator(dataset=self._dataset)
        self._sector_generator = SectorGenerator(dataset=self._dataset)
        self._legal_dataset = self._dataset

    @property
    def dataset(self) -> str:
        """Get the dataset.

        Returns:
            The dataset.
        """
        return self._dataset

    @property
    def company_name_generator(self) -> CompanyNameGenerator:
        """Get the company name generator.

        Returns:
            The company generator.
        """
        return self._company_name_generator

    @property
    def email_address_generator(self) -> EmailAddressGenerator:
        """Get the email address generator.

        Returns:
            The email address generator.
        """
        return self._email_address_generator

    @property
    def phone_number_generator(self) -> PhoneNumberGenerator:
        """Get the phone number generator.

        Returns:
            The phone number generator.
        """
        return self._phone_number_generator

    @property
    def address_generator(self) -> AddressGenerator:
        """Get the address generator.

        Returns:
            The address generator.
        """
        return self._address_generator

    @property
    def sector_generator(self) -> SectorGenerator:
        """Get the sector generator.

        Returns:
            The sector generator.
        """
        return self._sector_generator

    def get_legal_form(self) -> str:
        """Get a legal form.

        Returns:
            The legal form.
        """
        try:
            file_path = (
                Path(__file__).parent.parent.parent.parent
                / "domain_data"
                / "common"
                / "organization"
                / f"legalForm_{self._legal_dataset}.csv"
            )
            legal_values, legal_wgt = FileUtil.read_wgt_file(file_path)
        except Exception as e:
            logger.warning(
                f"Legal form data does not exist for dataset '{self._legal_dataset}', using 'US' as fallback: {e}"
            )
            self._legal_dataset = "US"
            file_path = (
                Path(__file__).parent.parent.parent.parent
                / "domain_data"
                / "common"
                / "organization"
                / f"legalForm_{self._legal_dataset}.csv"
            )
            legal_values, legal_wgt = FileUtil.read_wgt_file(file_path)
        return random.choices(legal_values, weights=legal_wgt, k=1)[0]
