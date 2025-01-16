# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


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
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_nestedKey_condition_with_defaultValue.xml", capture_test_result=True
        )
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

    def test_generate_with_condition(self):
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="test_generate_with_condition.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        result = engine.capture_result()

        containers = result["generate_container"]
        assert len(containers) == 6

        container_1 = result["container_1"]
        assert len(container_1) == 3 * 3
        for c_1 in container_1:
            assert c_1["lucky_1"] is not None
            assert isinstance(c_1["lucky_1"], float)

        container_2 = result["container_2"]
        assert len(container_2) == 3 * 1
        for c_2 in container_2:
            assert c_2["lucky_2"] is not None
            assert isinstance(c_2["lucky_2"], str)

        container_3 = result["sup_3|container_3"]
        assert len(container_3) == 3 * 2
        for c_3 in container_3:
            assert c_3["lucky_3"] is not None
            assert isinstance(c_3["lucky_3"], int)

        normal_condition = result["normal_condition"]
        assert len(normal_condition) == 10
        for n in normal_condition:
            normal_id = n["id"]
            assert normal_id in range(1, 11)
            lucky_1 = n.get("lucky_1")
            lucky_2 = n.get("lucky_2")
            lucky_3 = n.get("lucky_3")
            if normal_id % 2 == 0:
                assert lucky_1 is not None
                assert isinstance(lucky_1, float)
                assert lucky_2 is None
                assert lucky_3 is None
            elif normal_id % 3 == 0:
                assert lucky_1 is None
                assert lucky_2 is not None
                assert isinstance(lucky_2, str)
                assert lucky_3 is None
            else:
                assert lucky_1 is None
                assert lucky_2 is None
                assert lucky_3 is not None
                assert isinstance(lucky_3, int)
