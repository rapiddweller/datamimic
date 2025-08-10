# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestPrefixedWeightedIntPagination:
    _test_dir = Path(__file__).resolve().parent

    def test_prefixed_weighted_int_across_pages(self):
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="prefixed_weighted_int_pagination.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        result = engine.capture_result()["customer"]
        assert len(result) == 20001
        values = [int(row["custId_sparse"][1:]) for row in result]
        assert all(b > a for a, b in zip(values, values[1:], strict=False))
