# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datetime import datetime, timedelta

from datamimic_ce.generators.generator import Generator
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class BirthdateGenerator(Generator):
    """
    Purpose: generate a random birthdate between min_age and max_age.

    Use case (config):
        - Generate random birthdate (default age = 1 - 100).
        Example: birthdate_generator = BirthdateGenerator()
        - Generate specified birthdate with age (set: min = max = age).
        Example: birthdate_generator = BirthdateGenerator(20, 20)
        - Generate birthdate from min and max age.
        Example: birthdate_generator = BirthdateGenerator(20, 60)

    Attributes:
        min_age (int): minimum age value (inclusively).
        max_age (int): maximum age value (inclusively).
    """

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        min_age: int = 1,
        max_age: int = 100,
    ) -> None:
        """
        Parameters:
            min_age (int): minimum age value (inclusively).
            max_age (int): maximum age value (inclusively).

        Throws:
            ValueError: if min_age is higher than max_age
        """
        if min_age > max_age:
            raise ValueError("max_age must higher than or equals min_age")
        today = datetime.now()
        # if today is 29-02 of leap year, to avoid error, change it to 28-02
        if today.month == 2 and today.day == 29:
            today = datetime(today.year, 2, 28)
        self._min_birthdate = datetime(today.year - max_age - 1, today.month, today.day) + timedelta(days=1)
        self._max_birthdate = datetime(today.year - min_age, today.month, today.day)
        self._date_generator = class_factory_util.get_datetime_generator()(
            min=str(self._min_birthdate), max=str(self._max_birthdate), random=True
        )

    def generate(self) -> datetime:
        """
        generate random birthday between min and max age (calculated from today)

        Returns:
            datetime: generated date
        """
        return self._date_generator.generate()

    @staticmethod
    def convert_birthdate_to_age(birth_date: datetime) -> int:
        """
        age are calculated from given birthday and today
        (today value depends on system time and change over time, not fixed).

        Returns:
            age (int): calculated age (hour, minute, second, microsecond in datetime object equal 0 as default)
        """
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
