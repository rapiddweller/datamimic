# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestStatefulGeneratorPagination:
    _test_dir = Path(__file__).resolve().parent

    def test_stateful_generator_across_pages(self):
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="stateful_generator_pagination.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        result = engine.capture_result().get("customer")
        assert len(result) == 10001
        assert result[0]["id"] == 1
        assert result[9999]["id"] == 10000
        assert result[10000]["id"] == 10001
