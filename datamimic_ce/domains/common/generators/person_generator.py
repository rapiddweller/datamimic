# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path
from typing import Any
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.common.literal_generators.academic_title_generator import AcademicTitleGenerator
from datamimic_ce.domains.common.literal_generators.birthdate_generator import BirthdateGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.domains.common.literal_generators.gender_generator import GenderGenerator
from datamimic_ce.domains.common.literal_generators.given_name_generator import GivenNameGenerator
from datamimic_ce.domains.common.literal_generators.nobility_title_generator import NobilityTitleGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil
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
        from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil
        self._birthdate_generator = BirthdateGenerator(class_factory_util=ClassFactoryCEUtil())
        self._academic_title_generator = AcademicTitleGenerator(dataset=country_code)
        self._nobility_title_generator = NobilityTitleGenerator(dataset=country_code)

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

    @property
    def birthdate_generator(self) -> BirthdateGenerator:
        return self._birthdate_generator
    
    @property
    def academic_title_generator(self) -> AcademicTitleGenerator:
        return self._academic_title_generator
    
    @property
    def nobility_title_generator(self) -> NobilityTitleGenerator:
        return self._nobility_title_generator
    

    def load_salutation_data(self) -> dict[str, tuple[Any, ...]]:
        """Load salutation data from CSV file.

        Returns:
            A dictionary containing salutation data.
        """
        cache_key = f"salutation_data_{self._country_code}"

        if cache_key in self._LOADED_DATA_CACHE:
            return self._LOADED_DATA_CACHE[cache_key]
        
        salutation_file_path = Path(__file__).parent.parent.parent.parent/"domain_data"/"common"/"person" / f"salutation_{self._country_code}.csv"
        loaded_salutation_data = FileContentStorage.load_file_with_custom_func(cache_key=cache_key, read_func=lambda: FileUtil.read_csv_to_dict_of_tuples_with_header(salutation_file_path, delimiter=",")[0])

        self._LOADED_DATA_CACHE[cache_key] = loaded_salutation_data

        return loaded_salutation_data
    
    