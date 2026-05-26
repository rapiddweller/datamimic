# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import random
from pathlib import Path

from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.literal_generators.sector_generator import SectorGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import DatasetAwareDomainGenerator
from datamimic_ce.domains.utils.dataset_loader import pick_one_weighted_no_repeat
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class CompanyGenerator(DatasetAwareDomainGenerator):
    """Generator for company-related attributes.

    Provides methods to generate company-related attributes such as
    company names, emails, URLs, and other information.
    """

    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__(dataset=dataset, rng=rng)
        self._company_name_generator = CompanyNameGenerator(rng=self._derive_rng())
        self._email_address_generator = EmailAddressGenerator(
            dataset=self._dataset, rng=self._derive_rng()
        )
        self._phone_number_generator = PhoneNumberGenerator(
            dataset=self._dataset, rng=self._derive_rng()
        )
        self._address_generator = AddressGenerator(
            dataset=self._dataset, rng=self._derive_rng()
        )
        self._sector_generator = SectorGenerator(dataset=self._dataset, rng=self._derive_rng())
        self._legal_dataset = self._dataset
        self._last_legal_form: str | None = None

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
        file_path = dataset_path("common", "organization", f"legalForm_{self._legal_dataset}.csv", start=Path(__file__))
        legal_values, legal_wgt = FileUtil.read_wgt_file(file_path)
        choice = pick_one_weighted_no_repeat(self._rng, legal_values, legal_wgt, last=self._last_legal_form)
        self._last_legal_form = choice
        return choice
