# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


class TestPageProcess:
    _test_dir = Path(__file__).resolve().parent

    def test_simple_page_process_sp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_simple_page_process_sp.xml")
        engine.test_with_timer()

    def test_simple_page_process_mp(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_simple_simple_page_process_mp.xml")
        engine.test_with_timer()

    def test_consumer_csv(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_csv.xml")
        engine.test_with_timer()

    def test_consumer_json(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_json.xml")
        engine.test_with_timer()

    def test_consumer_xml(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_xml.xml")
        engine.test_with_timer()

    def test_consumer_txt(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_txt.xml")
        engine.test_with_timer()

    def test_consumer_sqlite(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="test_page_process_sqlite.xml")
        engine.test_with_timer()
