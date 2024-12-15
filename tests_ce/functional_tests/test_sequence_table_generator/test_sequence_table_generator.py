# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest
import pytest


class TestSequenceTableGenerator:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.asyncio
    async def test_sequence_table_generator_postgres(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="postgresql_test.xml", capture_test_result=True)
        await test_engine.test_with_timer()
        test_engine.capture_result()

    @pytest.mark.skip(reason="MySQL is not supported in this version")
    async def test_sequence_table_generator_mysql(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="mysql_test.xml", capture_test_result=True)
        await test_engine.test_with_timer()
        test_engine.capture_result()

    @pytest.mark.skip(reason="MSSQL is not supported in this version")
    async def test_sequence_table_generator_mssql(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="mssql_test.xml", capture_test_result=True)
        await test_engine.test_with_timer()
        test_engine.capture_result()
