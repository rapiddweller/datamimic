# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestConverter:
    _test_dir = Path(__file__).resolve().parent

    def test_remove_none_or_empty_element(self) -> None:
        engine = DataMimicTest(test_dir=self._test_dir,
                               filename="test_remove_none_or_empty_element.xml",
                               capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        groups = result["group"]
        assert len(groups) == 5

        for group in groups:
            assert group == {'nested_list': [{'inside_ele': 2}]}

    def test_remove_none_or_empty_element_more(self) -> None:
        engine = DataMimicTest(test_dir=self._test_dir,
                               filename="test_remove_none_or_empty_element_more.xml",
                               capture_test_result=True)
        engine.test_with_timer()

        result = engine.capture_result()
        groups = result["group"]
        assert len(groups) == 5

        for group in groups:
            assert group.get("none_value") is None

            assert isinstance(group["array"], list)
            assert len(group["array"]) == 0
            assert group["array"] == []

            assert isinstance(group["nested_list"], list)
            assert len(group["nested_list"]) == 2
            assert group["nested_list"] == [{}, {}]

            assert isinstance(group["nested_dict"], dict)
            assert len(group["nested_dict"]) == 0
            assert group["nested_dict"] == {}
