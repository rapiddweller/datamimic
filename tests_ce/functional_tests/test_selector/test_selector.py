# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestSelector:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_simple_selector(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_selector.xml", capture_test_result=True)
        await test_engine.test_with_timer()

        result = test_engine.capture_result()

        data = result["data"]

        assert len(data) == 17
        assert data[0]["user_id"] == 1

    @pytest.mark.asyncio
    async def test_iteration_selector(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_iteration_selector.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()

        assert result["simple_data"][:10] == result["iteration_data"][:10]

    @pytest.mark.asyncio
    async def test_dynamic_selector(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_dynamic_selector.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()

        assert len(result["generate_selector"]) == 17

        variable_selector = result["variable_selector"]
        for e in variable_selector:
            assert e.get("name") == f"Name {e.get('id')}"

    @pytest.mark.asyncio
    async def test_edit_dynamic_selector(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_edit_dynamic_selector.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()

        assert len(result["generate_selector"]) == 17

        variable_selector = result["variable_selector"]
        for e in variable_selector:
            assert e.get("name") == f"Name {e.get('id')}"

        assert len(result["generate_selector2"]) == 17

        variable_selector2 = result["variable_selector2"]
        for e in variable_selector2:
            assert e.get("name") == f"Name {e.get('id')}"
