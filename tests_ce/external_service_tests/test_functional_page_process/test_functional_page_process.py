# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestFunctionalPageProcess:
    _test_dir = Path(__file__).resolve().parent

    def test_page_process_mongo(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_page_process_mongo.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()

        motorcycles = result["motorcycles"]
        assert len(motorcycles) == 100
        assert motorcycles[10]["id"] == 11

        # multi-page ordered read (2 workers, pageSize 30): complete, no duplicates
        assert sorted(m["id"] for m in result["motorbike"]) == list(range(1, 101))
        # random read: disjoint windows of one global shuffle -> a permutation, not a sample
        assert sorted(m["id"] for m in result["motorbike_random"]) == list(range(1, 101))

    def test_page_process_postgres(self):
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="test_page_process_postgres.xml", capture_test_result=True
        )
        engine.test_with_timer()

        result = engine.capture_result()

        assert len(result["counter"]) == 10
        motorcycles = result["motorbike"]
        assert len(motorcycles) == 100
        # assert motorcycles[10]["id"] == 10
