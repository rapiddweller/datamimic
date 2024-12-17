# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestGenerate:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_simple_generate(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="simple_generate.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_generate_with_source(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="generate_with_source.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_count(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_count.xml")
        await test_engine.test_with_timer()
