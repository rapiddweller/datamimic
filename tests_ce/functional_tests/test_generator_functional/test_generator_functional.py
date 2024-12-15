# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from decimal import Decimal
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest
from datamimic_ce.generators.generator_util import GeneratorUtil
from datamimic_ce.utils.file_util import FileUtil


def count_digits_after_decimal(number):
    num_str = str(number)
    # Check if the string contains a decimal point
    if "." in num_str:
        # Find the index of the decimal point
        decimal_index = num_str.index(".")

        # Count the number of digits after the decimal point
        num_digits_after_decimal = len(num_str) - decimal_index - 1

        return num_digits_after_decimal
    else:
        # If there's no decimal point, return 0
        return 0


class TestDatamimicGeneratorFunctional:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_uuid_generator(self) -> None:
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="uuid_generator_test.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        assert result

        result_uuid_list = result["uuid_generator_test"]
        for output_result in result_uuid_list:
            assert GeneratorUtil.is_valid_uuid(output_result["uuid_name"]) is True

    @pytest.mark.asyncio
    async def test_bank_generator(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="bank_generator_test.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        bank = result["bank"]
        assert len(bank) == 100

    @pytest.mark.asyncio
    async def test_bank_account_generator(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="bank_account_generator_test.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        bank_account = result["bank_account"]
        assert len(bank_account) == 100

    @pytest.mark.asyncio
    async def test_float_generator(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="float_generator_test.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        float_generator = result["float_generator"]
        assert len(float_generator) == 100
        for e in float_generator:
            assert isinstance(e.get("no_param"), float)
            assert 0 <= e.get("no_param") <= 10
            assert isinstance(e.get("min_param"), float)
            assert 9 <= e.get("min_param") <= 10
            assert isinstance(e.get("max_param"), float)
            assert 0 <= e.get("max_param") <= 100
            assert isinstance(e.get("full_param"), float)
            assert 10 <= e.get("full_param") <= 20
            assert Decimal(str(e.get("full_param"))) % Decimal(str(0.0003)) == 0

        assert any(count_digits_after_decimal(element.get("granularity_param")) == 2 for element in float_generator)
        assert any(count_digits_after_decimal(element.get("full_param")) == 4 for element in float_generator)

    @pytest.mark.asyncio
    async def test_name_generator(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="name_generator_test.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        container = result["container"]
        assert container is not None
        name_test = result["name_test"]
        assert name_test is not None
        assert len(name_test) == len(container) * 10

    @pytest.mark.asyncio
    async def test_academic_title_generator(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="academic_title_generator_test.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        academic_title = result["academic_title"]
        assert len(academic_title) == 100
        prefix = self._test_dir.parent.parent.parent

        titles, weights = FileUtil.read_wgt_file(
            prefix.joinpath("datamimic_ce/generators/data/person/title.csv"), delimiter=","
        )
        cn_titles, cn_weights = FileUtil.read_wgt_file(
            prefix.joinpath("datamimic_ce/generators/data/person/title_CN.csv"), delimiter=","
        )
        de_titles, de_weights = FileUtil.read_wgt_file(
            prefix.joinpath("datamimic_ce/generators/data/person/title_DE.csv"), delimiter=","
        )
        fr_titles, fr_weights = FileUtil.read_wgt_file(
            prefix.joinpath("datamimic_ce/generators/data/person/title_FR.csv"), delimiter=","
        )
        it_titles, it_weights = FileUtil.read_wgt_file(
            prefix.joinpath("datamimic_ce/generators/data/person/title_IT.csv"), delimiter=","
        )
        us_titles, us_weights = FileUtil.read_wgt_file(
            prefix.joinpath("datamimic_ce/generators/data/person/title_US.csv"), delimiter=","
        )

        for element in academic_title:
            assert element["non-title"] == ""
            assert element["title"] in titles
            assert element["CN-title"] in cn_titles
            assert element["DE-title"] in de_titles
            assert element["FR-title"] in fr_titles
            assert element["IT-title"] in it_titles
            assert element["US-title"] in us_titles

    @pytest.mark.asyncio
    async def test_gender_generator(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="gender_generator_test.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        valid_genders = ["female", "male", "other"]
        gender_test = result["gender_test"]
        assert len(gender_test) == 1000
        default_values = list()
        for element in gender_test:
            assert element["female_gender"] == "female"
            assert element["other_gender"] == "other"
            assert element["male_gender"] == "male"
            assert element["default_gender"] in valid_genders
            default_values.append(element["default_gender"])

        # Check if all gender are present in default_values
        assert all(gender in default_values for gender in valid_genders)
