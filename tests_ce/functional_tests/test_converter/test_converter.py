# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestConverter:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_remove_none_or_empty_element(self) -> None:
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_remove_none_or_empty_element.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        groups = result["group"]
        assert len(groups) == 5

        for group in groups:
            assert group == {"nested_list": [{"inside_ele": 2}]}

    @pytest.mark.asyncio
    async def test_remove_none_or_empty_element_more(self) -> None:
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_remove_none_or_empty_element_more.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
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
