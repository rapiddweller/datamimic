# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path
from unittest import TestCase

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestCondition(TestCase):
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_condition(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_condition.xml", capture_test_result=True)
        await test_engine.test_with_timer()
        result = test_engine.capture_result()

        bikes = result["bike"]
        assert len(bikes) == 100
        for bike in bikes:
            if bike["year"] < 2000:
                assert bike["attributes"] is not None
                assert bike["list"][1] is not None
                assert bike["list"][1]["ele_year"] == bike["year"]
                if bike["id"] % 2 == 1:
                    assert bike["attributes"]["serial"] is not None
                    assert bike["list"][0] is not None
                    assert bike["list"][0]["ele_id"] == bike["attributes"]["serial"]
                else:
                    with pytest.raises(KeyError):
                        bike["attributes"]["serial"]
            else:
                with pytest.raises(KeyError):
                    bike["attributes"]

    @pytest.mark.asyncio
    async def test_condition_with_defaultValue(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_nestedKey_condition_with_defaultValue.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()

        bikes = result["bike"]
        assert len(bikes) == 100
        for bike in bikes:
            assert bike["condition_true"] is not None
            if bike["id"] % 2 == 1:
                assert bike["condition_true"]["serial"] is not None

            assert bike["condition_false"] is None

            condition_2023 = bike["condition_2023"]
            if bike["year"] == 2023:
                assert isinstance(condition_2023, dict)
                assert condition_2023["serial"] is not None
            else:
                assert condition_2023 == 2023

            if bike["year"] == 1970:
                assert isinstance(bike["condition_false_non_default"], dict)
                assert bike["condition_false_non_default"]["serial"] is not None
            else:
                with self.assertRaises(KeyError):
                    bike["condition_false_non_default"]

            assert bike["same_name"]["age"] == 35

            assert bike["if_true"] is not None

            with self.assertRaises(KeyError):
                assert bike["if_false"]
