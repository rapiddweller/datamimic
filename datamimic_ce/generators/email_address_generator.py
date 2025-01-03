# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from typing import cast

from datamimic_ce.generators.domain_generator import DomainGenerator
from datamimic_ce.generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.generators.generator import Generator
from datamimic_ce.generators.given_name_generator import GivenNameGenerator


class EmailAddressGenerator(Generator):
    """
    Generates Email Addresses
    Can pass in given_name and family_name to make the email follow the name structure
    """

    def __init__(
        self,
        dataset: str,
        generated_count: int,
        given_name: str | None = None,
        family_name: str | None = None,
    ):
        self._given_name = given_name
        self._given_name_generator = (
            GivenNameGenerator(dataset=dataset, generated_count=generated_count) if given_name is None else None
        )
        self._family_name = family_name
        self._family_name_generator = (
            FamilyNameGenerator(dataset=dataset, generated_count=generated_count) if family_name is None else None
        )
        self._company_name: str | None = None
        self._domain_generator = DomainGenerator(generated_count=generated_count)

    def generate(self) -> str:
        """
        create a email address
        """
        given_name_generator = cast(GivenNameGenerator, self._given_name_generator)
        family_name_generator = cast(FamilyNameGenerator, self._family_name_generator)

        given_name = str(self._given_name or given_name_generator.generate()).lower()
        family_name = str(self._family_name or family_name_generator.generate()).lower()
        if self._company_name:
            domain = self._domain_generator.generate_with_company_name(self._company_name).lower()
        else:
            domain = self._domain_generator.generate().lower()

        join = random.choice(["_", ".", "0", "1"])
        if join == "0":
            return f"{given_name}{family_name}@{domain}"
        elif join == "1":
            return f"{given_name[0]}{family_name}@{domain}"
        else:
            return f"{given_name}{join}{family_name}@{domain}"

    def generate_with_company_name(self, company_name: str):
        """
        Generate with specific company name

        :param company_name:
        :return:
        """
        self._company_name = company_name
        return self.generate()

    def generate_with_name(self, given_name: str, family_name: str):
        """
        Generate with specific company name

        :param company_name:
        :return:
        """
        self._given_name = given_name
        self._family_name = family_name
        return self.generate()
