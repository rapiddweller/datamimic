# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestDatamimicGenerator:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_date_generate_with_descriptor(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="date_generator_test.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_standalone_generator(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="standalone_generator_test.xml")
        await test_engine.test_with_timer()
