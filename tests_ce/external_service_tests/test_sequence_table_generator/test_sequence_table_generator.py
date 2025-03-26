# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestSequenceTableGenerator:
    _test_dir = Path(__file__).resolve().parent

    def test_sequence_table_generator_postgres(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="postgresql_test.xml", capture_test_result=True)
        engine.test_with_timer()
        engine.capture_result()

    @pytest.mark.skip(reason="MySQL is not supported in this version")
    def test_sequence_table_generator_mysql(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="mysql_test.xml", capture_test_result=True)
        engine.test_with_timer()
        engine.capture_result()

    @pytest.mark.skip(reason="MSSQL is not supported in this version")
    def test_sequence_table_generator_mssql(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="mssql_test.xml", capture_test_result=True)
        engine.test_with_timer()
        engine.capture_result()
