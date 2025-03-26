# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestSqlite:
    _test_dir = Path(__file__).resolve().parent

    def test_sqlite(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="datamimic.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()
        assert len(result) == 2

    def test_more_sqlite(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="more_sqlite_test.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()
        assert len(result) == 3
        simple_user = result["simple_user"]
        assert len(simple_user) == 10
        in_out = result["in_out"]
        assert len(in_out) == 10
        iterate_simple_user = result["iterate_simple_user"]
        assert iterate_simple_user == simple_user
