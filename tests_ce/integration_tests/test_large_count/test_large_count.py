# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestLargeCount:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_large_count(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_large_count.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_large_count_2(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_large_count_2.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_builders(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_entities.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_generators(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_generators.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_new_builders(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_new_builders.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_large_count_small_page(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_large_count_small_page.xml")
        await test_engine.test_with_timer()
