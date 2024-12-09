# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



from pathlib import Path
from unittest import TestCase

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestCondition(TestCase):
    _test_dir = Path(__file__).resolve().parent

    def test_condition(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_condition.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

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

    def test_condition_with_defaultValue(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_nestedKey_condition_with_defaultValue.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

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
