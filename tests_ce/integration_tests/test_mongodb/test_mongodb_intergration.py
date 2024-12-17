# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.config import settings
from datamimic_ce.data_mimic_test import DataMimicTest


class TestMongoDB:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_mongodb_update(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_update.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_mongodb_selector(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_selector.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_mongodb_selector_mp(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_selector_mp.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_mongodb_upsert(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_upsert.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_mongodb_delete(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_delete.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_mongodb_query(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_query.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_mongodb_aggregate(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_aggregate.xml")
        await test_engine.test_with_timer()

    @pytest.mark.skipif(settings.RUNTIME_ENVIRONMENT != "development", reason="Run only on local")
    @pytest.mark.asyncio
    async def test_mongodb_local_env(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_local_env.xml")
        await test_engine.test_with_timer()

    @pytest.mark.skipif(settings.RUNTIME_ENVIRONMENT == "development", reason="Not run on local")
    @pytest.mark.asyncio
    async def test_mongodb_global_env(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_global_env.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_mongodb_dynamic_selector(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mongodb_dynamic_selector.xml")
        await test_engine.test_with_timer()
