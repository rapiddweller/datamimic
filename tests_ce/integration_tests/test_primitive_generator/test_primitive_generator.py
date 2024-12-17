# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestPrimitiveGenerator:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_primitive_generator(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_primitive_generator.xml")
        await test_engine.test_with_timer()
