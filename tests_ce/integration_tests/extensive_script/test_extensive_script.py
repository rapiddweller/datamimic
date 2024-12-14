# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestExtensiveScript:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_custom_script_components(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="custom_script_components/datamimic.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_custom_components_local_import_multiprocessing(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="local_global_import/multi_local.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_custom_components_local_import_single(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="local_global_import/single_local.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_custom_components_global_import_single(self) -> None:
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="local_global_import/single_global.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_custom_components_global_import_multiprocessing(self) -> None:
        error_message = "Global imports are not supported in multiprocessing mode."
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="local_global_import/multi_global.xml")
        with pytest.raises(Exception, match=error_message):
            await test_engine.test_with_timer()
