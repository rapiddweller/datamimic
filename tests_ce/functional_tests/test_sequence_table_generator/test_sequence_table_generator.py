# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



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
