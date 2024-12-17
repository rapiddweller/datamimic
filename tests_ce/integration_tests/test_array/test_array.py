# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestArray:
    @pytest.fixture
    def test_dir(self) -> Path:
        return Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_array_simple_types(self, test_dir: Path) -> None:
        test_engine = DataMimicTest(test_dir=test_dir, filename="test_array_simple_types.xml")
        await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_array_invalid_type(self, test_dir: Path) -> None:
        test_engine = DataMimicTest(test_dir=test_dir, filename="test_array_invalid_type.xml")
        with pytest.raises(ValueError):
            await test_engine.test_with_timer()

    @pytest.mark.asyncio
    async def test_array_script(self, test_dir: Path) -> None:
        test_engine = DataMimicTest(test_dir=test_dir, filename="test_array_script.xml")
        await test_engine.test_with_timer()
