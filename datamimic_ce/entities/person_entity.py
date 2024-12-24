# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import csv
import datetime
from pathlib import Path
from typing import Literal

from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.generators.academic_title_generator import AcademicTitleGenerator
from datamimic_ce.generators.birthdate_generator import BirthdateGenerator
from datamimic_ce.generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.generators.gender_generator import GenderGenerator
from datamimic_ce.generators.given_name_generator import GivenNameGenerator
from datamimic_ce.generators.nobility_title_generator import NobilityTitleGenerator
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


def calculate_age(birth_date: datetime.datetime) -> int:
    """
    Calculate the age based on the birth date.

    Args:
        birth_date (datetime.datetime): The birth date.

    Returns:
        int: The calculated age.
    """
    today = datetime.datetime.now()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def get_salutation(path: Path) -> dict[str, str]:
    """
    Read salutation from a CSV file and save it into a dictionary.

    Args:
        path (Path): The path to the CSV file.

    Returns:
        Dict[str, str]: A dictionary with salutations.
    """
    salutation_dict = {}

    with open(f"{path}") as file:
        reader = csv.DictReader(file, fieldnames=["FEMALE", "MALE"], delimiter=",")
        for row in reader:
            salutation_dict.update({"FEMALE": row["FEMALE"], "MALE": row["MALE"]})
    return salutation_dict


class PersonEntity:
    """
    Represents a person entity with various attributes.

    This class provides methods to generate and access person-related data.
    """

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        dataset: str,
        count: int,
        **kwargs,
    ):
        """
        Initialize the PersonEntity.

        Args:
            class_factory_util (BaseClassFactoryUtil): The class factory utility.
            dataset (str): The dataset to be used (e.g., "US", "EN", "CN", "BR").
            count (int): The number of items to generate for each attribute.
            **kwargs: Additional keyword arguments to customize the generation:
                - "min_age" (Optional[int]): The minimum age for the generated person. Defaults to 15 if not provided.
                - "max_age" (Optional[int]): The maximum age for the generated person. Defaults to 105 if not provided.
                - "female_quota" (Optional[float]): The quota of female names. Defaults to 0.49 if not provided.
                - "other_gender_quota" (Optional[float]): The quota of other gender. Defaults to 0.02 if not provided.
                - "noble_quota" (Optional[float]): The quota of person has noble title. Default 0.001.
                - "academic_title_quota" (Optional[float]): The quota of person has academic title. Default 0.5.
        """
        min_age = kwargs.get("min_age", 15)
        max_age = kwargs.get("max_age", 105)
        female_quota = kwargs.get("female_quota", 0.49)
        other_gender_quota = kwargs.get("other_gender_quota", 0.02)
        noble_quota = kwargs.get("noble_quota")
        academic_title_quota = kwargs.get("academic_title_quota", 0.5)

        birth_day_gen = BirthdateGenerator(class_factory_util, min_age=min_age, max_age=max_age)
        given_name_gen = GivenNameGenerator(dataset=dataset, generated_count=count)
        gender_gen = GenderGenerator(female_quota=female_quota, other_gender_quota=other_gender_quota)
        family_name_gen = FamilyNameGenerator(dataset=dataset, generated_count=count)
        academic_title_gen = AcademicTitleGenerator(dataset=dataset, quota=academic_title_quota)
        email_gen = EmailAddressGenerator(dataset=dataset, generated_count=count)
        nobility_title_gen = NobilityTitleGenerator(dataset=dataset, noble_quota=noble_quota)

        self._salutation_data = get_salutation(
            Path(__file__).parent.parent.joinpath(f"generators/data/person/salutation_{dataset.upper()}.csv")
        )

        generator_fn_dict = {
            "birth_day": lambda: birth_day_gen.generate(),
            "given_name": lambda: given_name_gen.generate_with_gender(self.gender),
            "gender": lambda: gender_gen.generate(),
            "family_name": lambda: family_name_gen.generate(),
            "academic_title": lambda: "" if self.age < 20 else academic_title_gen.generate(),
            "email": lambda: email_gen.generate_with_name(self.given_name, self.family_name),
            "age": lambda: calculate_age(self.birthdate),
            "salutation": lambda: "" if self.gender == "other" else self._salutation_data.get(self.gender.upper()),
            "nobility_title": lambda: nobility_title_gen.generate_with_gender(self.gender.lower()),
        }

        self._field_generator = EntityUtil.create_field_generator_dict(generator_fn_dict)

    @property
    def gender(self) -> Literal["male", "female", "other"]:
        """
        Get the gender of the person.

        Returns:
            str: The gender of the person.
        """
        return self._field_generator["gender"].get()

    @property
    def birthdate(self) -> datetime.datetime:
        """
        Get the birth date of the person.

        Returns:
            datetime.datetime: The birth date of the person.
        """
        return self._field_generator["birth_day"].get()

    @property
    def given_name(self) -> str:
        """
        Get the given name of the person.

        Returns:
            str: The given name of the person.
        """
        return self._field_generator["given_name"].get()

    @property
    def family_name(self) -> str:
        """
        Get the family name of the person.

        Returns:
            str: The family name of the person.
        """
        return self._field_generator["family_name"].get()

    @property
    def name(self) -> str:
        """
        Get the full name of the person.

        Returns:
            str: The full name of the person.
        """
        return f"{self.given_name} {self.family_name}"

    @property
    def email(self) -> str:
        """
        Get the email address of the person.

        Returns:
            str: The email address of the person.
        """
        return self._field_generator["email"].get()

    @property
    def academic_title(self) -> str:
        """
        Get the academic title of the person.

        Returns:
            str: The academic title of the person.
        """
        return self._field_generator["academic_title"].get()

    @property
    def age(self) -> int:
        """
        Get the age of the person.

        Returns:
            int: The age of the person.
        """
        return self._field_generator["age"].get()

    @property
    def salutation(self) -> str:
        """
        Get the salutation of the person.

        Returns:
            str: The salutation of the person.
        """
        return self._field_generator["salutation"].get()

    @property
    def nobility_title(self) -> str:
        """
        Get the nobility title of the person.

        Returns:
            str: The nobility title of the person.
        """
        return self._field_generator["nobility_title"].get()

    def reset(self):
        """
        Reset the field generators.

        This method resets all field generators to their initial state.
        """
        for value in self._field_generator.values():
            value.reset()
