# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestNestedGenerate:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_nested_generate(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_nested_generate.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        test_engine.capture_result()

    @pytest.mark.asyncio
    async def test_generate_as_source(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_generate_as_source.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        test_engine.capture_result()

    @pytest.mark.asyncio
    async def test_generate_as_source_2(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_generate_as_source_2.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()
        test_engine.capture_result()
