# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datetime import datetime

import pytest

from datamimic_ce.domains.common.literal_generators.birthdate_generator import BirthdateGenerator
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestBirthGenerator:
    # Test with 3 case[datetime, corresponding_age]
    _birthdate_case = [
        datetime(2010, 1, 20),
        datetime(1925, 1, 20),
        datetime(2022, 12, 31),
    ]

    @staticmethod
    def get_class_factory_util():
        return ClassFactoryCEUtil()

    def test_generate_birth_default(self):
        generator = BirthdateGenerator(self.get_class_factory_util())
        for i in range(1000):
            generated_date = generator.generate()
            assert generated_date is not None, "failed to generate date"
            assert 1 <= generator.convert_birthdate_to_age(generated_date) <= 100, f"Test {i + 1} failed"

    def test_convert_birthdate_to_age_method(self):
        generator = BirthdateGenerator(self.get_class_factory_util())
        current_date = datetime.now()
        for birthdate in self._birthdate_case:
            expected_age = (
                current_date.year
                - birthdate.year
                - ((current_date.month, current_date.day) < (birthdate.month, birthdate.day))
            )
            assert expected_age == generator.convert_birthdate_to_age(birthdate)

    @pytest.mark.parametrize(
        "min_age, max_age",
        [
            (1, 10),
            (25, 60),
            (20, 20),
        ],
    )
    def test_generate_birth_with_min_max_age(self, min_age, max_age):
        for _ in range(1000):
            generator = BirthdateGenerator(self.get_class_factory_util(), min_age, max_age)
            generated_date = generator.generate()
            assert generated_date is not None, "failed to generate date"
            assert min_age <= generator.convert_birthdate_to_age(generated_date) <= max_age

    def test_generate_birth_with_min_higher_than_max_age(self):
        min_age = 19
        max_age = 18
        with pytest.raises(ValueError, match="max_age must higher than or equals min_age"):
            BirthdateGenerator(self.get_class_factory_util(), min_age, max_age)
