# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

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
from datamimic_ce.utils.file_util import FileUtil


class PersonGenerator(BaseDomainGenerator):
    """Generator for person-related attributes.

    Provides methods to generate person-related attributes such as
    first name, last name, email address, phone number, and address.
    """

    def __init__(
        self,
        dataset: str | None = None,
        min_age: int = 18,
        max_age: int = 65,
        female_quota: float = 0.5,
        other_gender_quota: float = 0.0,
        noble_quota: float = 0.001,
        academic_title_quota: float = 0.5,
    ):
        self._dataset = dataset or "US"
        self._gender_generator = GenderGenerator(female_quota=female_quota, other_gender_quota=other_gender_quota)
        self._given_name_generator = GivenNameGenerator(dataset=self._dataset)
        self._family_name_generator = FamilyNameGenerator(dataset=self._dataset)
        self._email_generator = EmailAddressGenerator(dataset=self._dataset)
        self._phone_generator = PhoneNumberGenerator(dataset=self._dataset)
        self._address_generator = AddressGenerator(dataset=self._dataset)
        from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil

        self._birthdate_generator = BirthdateGenerator(
            class_factory_util=ClassFactoryCEUtil(), min_age=min_age, max_age=max_age
        )
        self._academic_title_generator = AcademicTitleGenerator(dataset=self._dataset, quota=academic_title_quota)
        self._nobility_title_generator = NobilityTitleGenerator(dataset=self._dataset, noble_quota=noble_quota)

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

    def get_salutation_data(self, gender: str) -> str:
        """Get salutation data from CSV file.

        Returns:
            A dictionary containing salutation data.
        """

        salutation_file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "common"
            / "person"
            / f"salutation_{self._dataset}.csv"
        )
        header_dict, data = FileUtil.read_csv_to_dict_of_tuples_with_header(salutation_file_path, delimiter=",")

        return data[0][header_dict[gender]] if gender in header_dict else ""
