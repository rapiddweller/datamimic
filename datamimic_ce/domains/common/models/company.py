# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.property_cache import property_cache
from datamimic_ce.domains.common.generators.company_generator import CompanyGenerator
from datamimic_ce.domains.common.models.address import Address


class Company(BaseEntity):
    """Company entity model representing a business organization.

    This class provides access to company data including name, sector, email, URL, phone number,
    office phone number, fax, address, and more.
    """

    def __init__(self, company_generator: CompanyGenerator):
        """Initialize a company entity.

        Args:
            company_generator: Company generator instance
        """
        super().__init__()
        self._company_generator = company_generator

    @property
    @property_cache
    def id(self) -> str:
        """Get the ID of the company.

        Returns:
            The ID of the company
        """
        return self.short_name.lower().replace(" ", "_")

    @property
    @property_cache
    def short_name(self) -> str:
        """Get the short name of the company.

        Returns:
            The short name of the company
        """
        return self._company_generator.company_name_generator.generate()

    @property
    @property_cache
    def sector(self) -> str | None:
        """Get the sector in which the company operates.

        Returns:
            The sector in which the company operates
        """
        return self._company_generator.sector_generator.generate()

    @property
    @property_cache
    def legal_form(self) -> str:
        """Get the legal form of the company.

        Returns:
            The legal form of the company
        """
        return self._company_generator.get_legal_form()

    @property
    @property_cache
    def full_name(self) -> str:
        """Get the full name of the company.

        Returns:
            The full name of the company
        """
        legal_form = self.legal_form
        builder = []
        if self.short_name is not None:
            builder.append(self.short_name)
        if self.sector is not None:
            builder.append(self.sector)
        if legal_form is not None:
            builder.append(legal_form)
        return " ".join(builder)

    @property
    @property_cache
    def email(self) -> str:
        """Get the email address of the company.

        Returns:
            The email address of the company
        """
        return self._company_generator.email_address_generator.generate_with_company_name(self.short_name)

    @property
    @property_cache
    def url(self) -> str | None:
        """Get the URL of the company.

        Returns:
            The URL of the company
        """
        scheme = random.choice(["http", "https"])
        company_email_domain = self.email.split("@")[1]
        return f"{scheme}://{company_email_domain}"

    @property
    @property_cache
    def phone_number(self) -> str | None:
        """Get the phone number of the company.

        Returns:
            The phone number of the company
        """
        return self._company_generator.phone_number_generator.generate()

    @property
    @property_cache
    def office_phone(self) -> str | None:
        """Get the office phone number of the company.

        Returns:
            The office phone number of the company
        """
        return self._company_generator.phone_number_generator.generate()

    @property
    @property_cache
    def fax(self) -> str | None:
        """Get the fax number of the company.

        Returns:
            The fax number of the company
        """
        return self._company_generator.phone_number_generator.generate()

    @property
    @property_cache
    def address_data(self) -> Address:
        """Get the address of the company.

        Returns:
            The address of the company
        """
        return Address(self._company_generator.address_generator)

    @property
    @property_cache
    def street(self) -> str:
        """Get the street address of the company.

        Returns:
            The street address of the company
        """
        return self.address_data.street

    @property
    @property_cache
    def house_number(self) -> str:
        """Get the house number of the company.

        Returns:
            The house number of the company
        """
        return self.address_data.house_number

    @property
    @property_cache
    def city(self) -> str:
        """Get the city where the company is located.

        Returns:
            The city where the company is located
        """
        return self.address_data.city

    @property
    @property_cache
    def state(self) -> str | None:
        """Get the state where the company is located.

        Returns:
            The state where the company is located
        """
        return self.address_data.state

    @property
    @property_cache
    def zip_code(self) -> str:
        """Get the zip code of the company.

        Returns:
            The zip code of the company
        """
        return self.address_data.zip_code

    @property
    @property_cache
    def country(self) -> str:
        """Get the country where the company is located.

        Returns:
            The country where the company is located
        """
        return self.address_data.country

    @property
    @property_cache
    def country_code(self) -> str:
        """Get the country code of the company.

        Returns:
            The country code of the company
        """
        return self._company_generator.dataset

    def to_dict(self) -> dict:
        """Convert company entity to a dictionary.

        Returns:
            Dictionary representation of the company
        """
        return {
            "short_name": self.short_name,
            "sector": self.sector,
            "email": self.email,
            "url": self.url,
            "phone_number": self.phone_number,
            "office_phone": self.office_phone,
            "fax": self.fax,
            "street": self.street,
            "house_number": self.house_number,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "country_code": self.country_code,
        }
