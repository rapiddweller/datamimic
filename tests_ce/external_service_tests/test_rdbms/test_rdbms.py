# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.config import settings
from datamimic_ce.data_mimic_test import DataMimicTest


class TestRdbms:
    _test_dir = Path(__file__).resolve().parent

    @pytest.mark.skipif(
        settings.RUNTIME_ENVIRONMENT == "production",
        reason="This test can only test with local postgres credential",
    )
    def test_postgresql_local(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_postgresql_local.xml")
        test_engine.test_with_timer()

    @pytest.mark.skipif(
        settings.RUNTIME_ENVIRONMENT == "development",
        reason="This test can only test with stage postgres credential",
    )
    def test_postgresql_stage(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_postgresql_stage.xml")
        test_engine.test_with_timer()

    @pytest.mark.skipif(
        settings.RUNTIME_ENVIRONMENT == "development",
        reason="This test can only test with stage postgres credential",
    )
    def test_mysql(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mysql.xml")
        test_engine.test_with_timer()

    @pytest.mark.skipif(
        settings.RUNTIME_ENVIRONMENT == "development",
        reason="This test can only test with stage postgres credential",
    )
    def test_mssql(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_mssql.xml")
        test_engine.test_with_timer()

    @pytest.mark.skip(reason="Need to reconfigure the oracle connection")
    def test_oracle(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_oracle.xml")
        test_engine.test_with_timer()

    def test_sqlite(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="test_sqlite.xml")
        test_engine.test_with_timer()
