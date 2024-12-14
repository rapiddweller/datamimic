# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestSourceScripted:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_source_scripted(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_source_scripted.xml", capture_test_result=False
        )
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_default_source_scripted(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_default_source_scripted.xml", capture_test_result=False
        )
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_source_script_in_generate(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_source_scripted_in_generate.xml", capture_test_result=False
        )
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_source_scripted_in_nested_key(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_source_scripted_in_nested_key.xml", capture_test_result=False
        )
        await test_engine.test_with_timer()
