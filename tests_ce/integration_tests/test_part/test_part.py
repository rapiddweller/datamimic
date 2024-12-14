# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestPart:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_simple_part(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_part.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_source_part_json(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_source_part_json.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_source_part_csv(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_source_part_csv.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_part_within_iterate(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="part_in_iterate.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_script_dict(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_script_dict.xml")
        await test_engine.test_with_timer()
