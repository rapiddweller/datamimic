# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import os
import shutil
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestML:
    _test_dir = Path(__file__).resolve().parent

    def test_ml_train_database(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_ml_train_database.xml", capture_test_result=True
        )
        test_engine.test_with_timer()
        result = test_engine.capture_result()

        new_customer = result["NEW_CUSTOMER"]
        assert len(new_customer) == 5000

    def test_ml_train_memstore(self):
        test_engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_ml_train_memstore.xml", capture_test_result=True
        )
        test_engine.test_with_timer()
        result = test_engine.capture_result()

        new_customer = result["NEW_CUSTOMER"]
        assert len(new_customer) == 10000

        # delete result folder
        folder_path = self._test_dir.joinpath("output")
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
