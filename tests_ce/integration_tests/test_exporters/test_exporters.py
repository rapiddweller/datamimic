# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestExporter:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_multi_json(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="multi_json.xml")
            await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_single_csv(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="single_csv.xml")
            await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_single_combined(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="single_combine_all.xml")
            await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_single_cascaded_cases(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="single_cascaded_cases.xml")
            await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_multi_xml(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="multi_xml.xml")
        await test_engine.test_with_timer()
