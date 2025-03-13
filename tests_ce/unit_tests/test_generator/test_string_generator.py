# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import re

import pytest

from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestStringGenerator:
    @staticmethod
    def get_class_factory_util():
        return ClassFactoryCEUtil()

    @pytest.mark.parametrize(
        "min_length, max_length, char_set, unique, prefix, suffix",
        [
            (1, 10, "[a-zA-Z0-9]", True, "", ""),
            (25, 60, r"\d", False, "", ""),
            (14, 20, "[a-zA-Z0-9]", False, "pre", "suf"),
            (10, 20, "", False, "pre", "suf"),
        ],
    )
    def test_string_generator_valid(
        self, min_length: int, max_length: int, char_set: str, prefix: str, suffix: str, unique: bool
    ):
        if not char_set:
            char_set = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        print(char_set)
        generator = StringGenerator(
            self.get_class_factory_util(),
            min_len=min_length,
            max_len=max_length,
            char_set=char_set,
            unique=unique,
            prefix=prefix,
            suffix=suffix,
        )
        for _ in range(10):
            generated_string = generator.generate()
            assert isinstance(generated_string, str), "Generated value is not a string"

    def test_string_generator_invalid(self):
        with pytest.raises(
            ValueError, match=re.escape("Failed when init StringGenerator because min_len(9) > max_len(4)")
        ):
            StringGenerator(self.get_class_factory_util(), min_len=9, max_len=4).generate()

    def test_string_generator_unique_true_limit_charset(self):
        with pytest.raises(
            ValueError, match=re.escape("Cannot generate unique string with length 9 from character set of size 5")
        ):
            StringGenerator(
                self.get_class_factory_util(), char_set="[a-b]", min_len=5, max_len=9, unique=True
            ).generate()
