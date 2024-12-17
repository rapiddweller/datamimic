# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestStringInKeyVariableNode:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_string_with_key(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_string_with_key.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        query = result["test_string_key"]
        assert len(query) == 3
        for e in query:
            assert e["query"] == "find: 'orders', filter: 'status': 'active', 'priority': 'high'"

    @pytest.mark.asyncio
    async def test_string_variable(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_string_in_variable.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        query = result["test_string_variable"]
        assert len(query) == 3
        for e in query:
            assert e["query"] == "find: 'ordered'"

    @pytest.mark.asyncio
    async def test_string_multiple_variable(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_string_multiple_variable.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        query = result["test_string_multiple_variable"]
        assert len(query) == 3
        for e in query:
            assert e["query"] == "find: 'classA'"

    @pytest.mark.asyncio
    async def test_string_multiple_key(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_string_multiple_key.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        result = test_engine.capture_result()
        query = result["test_string_multiple_key"]
        assert len(query) == 3
        for e in query:
            assert e["shipping_card_2"] == "'package' is being prepared."
            assert e["shipping_card_3"] == "'package' has already been shipped."
            assert e["shipping_card_4"] == "Now 'package' has arrived to your address."
            assert (
                e["shipping_card_5"]
                == "Details of shipping card: 'package' is being prepared. 'package' has already been shipped. 'package' has already been shipped."
            )
