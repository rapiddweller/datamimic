# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Large-row-count descriptors, run only on explicit request."""

from pathlib import Path

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


class TestLargeCount:
    _test_dir = Path(__file__).resolve().parent

    def test_large_count(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_large_count.xml")
        engine.test_with_timer()

    def test_large_count_2(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_large_count_2.xml")
        engine.test_with_timer()

    def test_large_count_small_page(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_large_count_small_page.xml")
        engine.test_with_timer()
