# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import re

import pytest

from datamimic_ce.domains.shared.literal_generators.data_faker_generator import DataFakerGenerator


class TestFakerGenerator:
    def test_generate(self):
        for _ in range(100):
            generate_int = DataFakerGenerator(method="random_int", locale="de", min=0, max=15, step=3).generate()
            generate_given_name = DataFakerGenerator(method="first_name_female", locale="zh").generate()
            generate_family_name = DataFakerGenerator(method="last_name_female", locale="zh").generate()
            generate_company = DataFakerGenerator(method="company").generate()

            assert 0 <= generate_int <= 15
            assert isinstance(generate_given_name, str)
            assert isinstance(generate_family_name, str)
            assert isinstance(generate_company, str)

            chinese_name = generate_family_name + generate_given_name
            zh_characters = ""
            # find all Chinese characters
            for c in re.findall(r"[\u4e00-\u9fff]+", chinese_name):
                zh_characters += c
            assert len(chinese_name) == len(zh_characters)

    def test_args_generate(self):
        for _ in range(100):
            three_digit_number = DataFakerGenerator("random_number", None, 3, True).generate()
            assert 999 >= three_digit_number >= 100

    def test_kwargs_generate(self):
        for _ in range(100):
            three_digit_number = DataFakerGenerator("random_number", None, digits=3, fix_len=True).generate()
            assert 999 >= three_digit_number >= 100

    def test_args_kwargs_generate(self):
        for _ in range(100):
            three_digit_number = DataFakerGenerator("random_number", None, 3, fix_len=True).generate()
            assert 999 >= three_digit_number >= 100

    def test_invalid_method(self):
        invalid_method = "_invalid_method"
        with pytest.raises(ValueError) as error:
            DataFakerGenerator(method=invalid_method).generate()
        assert str(error.value) == f"Faker method '{invalid_method}' is not supported"

    def test_not_exist_method(self):
        invalid_method = "not_exist_method"
        with pytest.raises(ValueError) as error:
            DataFakerGenerator(method=invalid_method).generate()
        assert str(error.value) == f"Wrong Faker method: {invalid_method} does not exist"

    def test_provider_collection_is_not_a_faker_method(self):
        with pytest.raises(ValueError, match="Wrong Faker method: providers does not exist"):
            DataFakerGenerator(method="providers").generate()

    def test_valid_method_argument_errors_are_preserved(self):
        with pytest.raises(TypeError):
            DataFakerGenerator(method="random_int", unexpected_argument=True).generate()
