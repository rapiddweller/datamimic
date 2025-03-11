# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.generators.gender_generator import GenderGenerator
from datamimic_ce.generators.given_name_generator import GivenNameGenerator
from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator

class PersonGenerator(BaseDomainGenerator):
    """Generator for person-related attributes.
    
    Provides methods to generate person-related attributes such as
    first name, last name, email address, phone number, and address.
    """
    def __init__(self, country_code: str = "US"):
        self._country_code = country_code
        self._gender_generator = GenderGenerator()
        self._given_name_generator = GivenNameGenerator(dataset=country_code)
        self._family_name_generator = FamilyNameGenerator(dataset=country_code)
        self._email_generator = EmailAddressGenerator(dataset=country_code)
        self._phone_generator = PhoneNumberGenerator(dataset=country_code)
        self._address_generator = AddressGenerator(country_code=country_code)

    @property   
    def gender_generator(self) -> GenderGenerator:
        return self._gender_generator
    
    @property
    def given_name_generator(self) -> GivenNameGenerator:
        return self._given_name_generator
    
    @property   
    def family_name_generator(self) -> FamilyNameGenerator:
        return self._family_name_generator
    
    @property
    def email_generator(self) -> EmailAddressGenerator:
        return self._email_generator

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator
    
    @property
    def phone_generator(self) -> PhoneNumberGenerator:
        return self._phone_generator
