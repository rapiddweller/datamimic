# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestDataIteration:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_simple_csv(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_csv.xml", capture_test_result=True)
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        assert result["product1"] == result["product2"]

    @pytest.mark.asyncio
    async def test_weight_csv(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_weight_csv.xml", capture_test_result=True)
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        assert all(len(product) == 2 for product in result["product1"])
        assert all(len(product) == 2 for product in result["product2"])

    @pytest.mark.asyncio
    async def test_weight_ent_csv(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_weight_ent_csv.xml", capture_test_result=True
        )
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        assert all(len(product) == 3 for product in result["people1"])
        assert all(len(product) == 3 for product in result["people2"])

    @pytest.mark.asyncio
    async def test_part(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_part_csv.xml", capture_test_result=True)
        await test_engine.test_with_timer()

        result = test_engine.capture_result()
        assert result["people1"] == result["people2"]
