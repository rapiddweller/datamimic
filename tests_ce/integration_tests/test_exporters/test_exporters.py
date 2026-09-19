# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import shutil
from pathlib import Path

from lxml import etree

from datamimic_ce.data_mimic_test import DataMimicTest


class TestExporter:
    _test_dir = Path(__file__).resolve().parent

    def test_multi_json(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="multi_json.xml")
            test_engine.test_with_timer()

    def test_single_csv(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="single_csv.xml")
            test_engine.test_with_timer()

    def test_single_combined(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="single_combine_all.xml")
            test_engine.test_with_timer()

    def test_single_cascaded_cases(self):
        for _i in range(1):
            test_engine = DataMimicTest(test_dir=self._test_dir, filename="single_cascaded_cases.xml")
            test_engine.test_with_timer()

    def test_multi_xml(self):
        test_engine = DataMimicTest(test_dir=self._test_dir, filename="multi_xml.xml")
        test_engine.test_with_timer()

    def test_non_utf8_encoding_is_declared(self, tmp_path: Path):
        shutil.copy(self._test_dir / "non_utf8_encoding.xml", tmp_path)
        DataMimicTest(test_dir=tmp_path, filename="non_utf8_encoding.xml").test_with_timer()
        outputs = sorted((tmp_path / "output").rglob("people*.xml"))
        assert [p.name for p in outputs] == ["people.dbunit.xml", "people.xml"]
        for output in outputs:
            # Parse raw bytes: the parser must take the encoding from the declaration.
            root = etree.fromstring(output.read_bytes())
            assert "Müller" in etree.tostring(root, encoding="unicode"), output.name
