# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestVariable:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_variable(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable.xml", capture_test_result=True)
        await test_engine.test_with_timer()

        # Verify the variable exists before accessing
        result = test_engine.capture_result()
        assert result is not None, "No result captured"

    @pytest.mark.asyncio
    async def test_setup_context_variable(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_setup_context_variable.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_query_setup_context_variable(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_query_setup_context_variable.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_variable_with_same_name(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_with_same_name.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_variable_with_selector(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_with_selector.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_variable_with_type(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_with_type.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_variable_source_with_name_only(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_variable_source_with_name_only.xml")
        await test_engine.test_with_timer()

    @pytest.mark.skip("This test is not ready yet.")
    @pytest.mark.asyncio
    async def test_memstore_access(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_memstore_access.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_string_in_key(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_order_status.xml")
        await test_engine.test_with_timer()
