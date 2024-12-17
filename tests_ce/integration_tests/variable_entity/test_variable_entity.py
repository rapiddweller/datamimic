# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestVariableEntity:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_person_entity(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_person_entity.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_company_entity(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_company_entity.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_city_entity(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_city_entity.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_address_entity(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_address_entity.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_credit_card_entity(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_credit_card_entity.xml")
        await test_engine.test_with_timer()
