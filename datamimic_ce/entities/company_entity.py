# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from collections.abc import Callable
from pathlib import Path
from typing import cast

import numpy as np

from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import FieldGenerator
from datamimic_ce.generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.file_util import FileUtil


def full_name_gen(
    short_name: str,
    sector: str,
    legal_values: list,
    legal_wgt: list,
) -> str:
    """Generate the full name of the company.

    Args:
        short_name (str): The short name of the company.
        sector (str): The sector in which the company operates.
        legal_values (list): List of legal forms.
        legal_wgt (list): Weights for the legal forms.

    Returns:
        str: The full name of the company.

    """
    legal_form = random.choices(legal_values, legal_wgt, k=1)[0] if legal_values is not None else None
    builder = [""] if short_name is None else [short_name]
    if sector is not None:
        builder.append(" " + sector)
    if legal_form is not None:
        builder.append(" " + legal_form)
    return "".join(builder)


def email_gen(company_email_gen: EmailAddressGenerator, short_name: str) -> str:
    """Generate the email address for the company.

    Args:
        company_email_gen (EmailAddressGenerator): The email address generator.
        short_name (str): The short name of the company.

    Returns:
        str: The generated email address.

    """
    return company_email_gen.generate_with_company_name(short_name)


def url_gen(company_email: str) -> str | None:
    """Generate the URL for the company.

    Args:
        company_email (str): The email address of the company.

    Returns:
        Optional[str]: The generated URL or None if the email is None.

    """
    if company_email is None:
        return None

    list_of_schemes = ["http", "https"]
    scheme = np.random.choice(list_of_schemes)
    company_domain = company_email.split("@")[1]
    return f"{scheme}://{company_domain}"


class CompanyEntity(Entity):
    """Represents a company entity with various attributes.

    This class inherits from the Entity class and provides additional
    attributes and methods specific to a company entity.
    """

    def __init__(
        self,
        cls_factory_util: BaseClassFactoryUtil,
        locale: str,
        dataset: str,
        count: int,
    ) -> None:
        """Initialize the CompanyEntity.

        Args:
            cls_factory_util (BaseClassFactoryUtil): The class factory utility.
            locale (str): The locale for the company.
            dataset (str): The dataset to be used.
            count (int): The count of generated entities.

        """
        super().__init__(locale, dataset)
        self._dataset = dataset
        # Load file data
        self._sector = FileUtil.read_csv_having_single_column(
            Path(__file__).parent / f"data/organization/sector_{self._locale}.csv",
        )
        self._legal_values, self._legal_wgt = FileUtil.read_wgt_file(
            Path(__file__).parent / f"data/organization/legalForm_{self._dataset}.csv",
        )

        # Address builder is used to determine company location
        self._address_entity = AddressEntity(
            class_factory_util=cls_factory_util,
            dataset=dataset,
        )
        self._phone_number_generator = PhoneNumberGenerator(dataset=self._dataset)
        self._company_email_gen = EmailAddressGenerator(
            dataset=self._dataset,
            generated_count=count,
        )

        company_name_gen = CompanyNameGenerator()
        generator_fn_dict = {
            "id": lambda short_name: short_name.lower().replace(" ", "_") if short_name is not None else None,
            "short_name": lambda: company_name_gen.generate(),
            "city": lambda: self._address_entity.city,
            "country": lambda: self._address_entity.country,
            "street": lambda: self._address_entity.street,
            "state": lambda: self._address_entity.state,
            "zip_code": lambda: self._address_entity.zip_code,
            "house_number": lambda: self._address_entity.house_number,
            "sector": lambda: random.choice(self._sector) if self._sector is not None else None,
            "full_name": lambda short_name, sector: full_name_gen(
                short_name,
                sector,
                self._legal_values,
                self._legal_wgt,
            ),
            "email": lambda short_name: email_gen(self._company_email_gen, short_name),
            "phone_number": lambda: self._phone_number_generator.generate(),
            "office_phone": lambda: self._phone_number_generator.generate(),
            "fax": lambda: self._phone_number_generator.generate(),
            "url": lambda company_email: url_gen(company_email),
        }
        self._field_generator = {}
        for key, val in generator_fn_dict.items():
            self._field_generator[key] = FieldGenerator(cast(Callable, val))

    @property
    def id(self):
        """Get the ID of the company.

        Returns:
            str: The ID of the company.

        """
        return self._field_generator["id"].get(self.short_name)

    @property
    def short_name(self):
        """Get the short name of the company.

        Returns:
            str: The short name of the company.

        """
        return self._field_generator["short_name"].get()

    @property
    def city(self):
        """Get the city where the company is located.

        Returns:
            str: The city where the company is located.

        """
        return self._field_generator["city"].get()

    @property
    def country(self):
        """Get the country where the company is located.

        Returns:
            str: The country where the company is located.

        """
        return self._field_generator["country"].get()

    @property
    def country_code(self):
        """Get the country code of the company.

        Returns:
            str: The country code of the company.

        """
        return self._dataset

    @property
    def street(self):
        """Get the street address of the company.

        Returns:
            str: The street address of the company.

        """
        return self._field_generator["street"].get()

    @property
    def state(self):
        """Get the state where the company is located.

        Returns:
            str: The state where the company is located.

        """
        return self._field_generator["state"].get()

    @property
    def zip_code(self):
        """Get the zip code of the company.

        Returns:
            str: The zip code of the company.

        """
        return self._field_generator["zip_code"].get()

    @property
    def sector(self):
        """Get the sector in which the company operates.

        Returns:
            str: The sector in which the company operates.

        """
        return self._field_generator["sector"].get()

    @property
    def house_number(self):
        """Get the house number of the company.

        Returns:
            str: The house number of the company.

        """
        return self._field_generator["house_number"].get()

    @property
    def full_name(self):
        """Get the full name of the company.

        Returns:
            str: The full name of the company.

        """
        return self._field_generator["full_name"].get(self.short_name, self.sector)

    @property
    def email(self):
        """Get the email address of the company.

        Returns:
            str: The email address of the company.

        """
        return self._field_generator["email"].get(self.short_name)

    @property
    def phone_number(self) -> str | None:
        """Get the phone number of the company.

        Returns:
            Optional[str]: The phone number of the company.

        """
        return self._field_generator["phone_number"].get()

    @property
    def office_phone(self) -> str | None:
        """Get the office phone number of the company.

        Returns:
            Optional[str]: The office phone number of the company.

        """
        return self._field_generator["office_phone"].get()

    @property
    def fax(self) -> str | None:
        """Get the fax number of the company.

        Returns:
            Optional[str]: The fax number of the company.

        """
        return self._field_generator["fax"].get()

    @property
    def url(self) -> str | None:
        """Get the URL of the company.

        Returns:
            Optional[str]: The URL of the company.

        """
        return self._field_generator["url"].get(self.email)

    def reset(self):
        """Reset the field generators and address entity."""
        for value in self._field_generator.values():
            value.reset()
        self._address_entity.reset()
